#!/usr/bin/env node

/**
 * Dependency-free JavaScript verifier for the published Agent ProofChain receipt vector.
 *
 * This demonstrates that the chain contract is portable beyond the Python implementation.
 * It validates the narrow vector used by the repository; it is not a production ledger store.
 */

import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const digestPattern = /^[0-9a-f]{64}$/;
const digestFields = [
  "content_sha256",
  "claimed_actor_sha256",
  "actor_family_sha256",
  "runtime_family_sha256",
  "capability_sha256",
  "action_sha256",
  "model_sha256",
  "source_sha256",
];
const requiredFields = new Set([
  "schema_version",
  "request_id",
  "allowed",
  "decision",
  "reason_codes",
  "content_sha256",
  "injection_matches",
  "claimed_actor_sha256",
  "actor_family_sha256",
  "runtime_family_sha256",
  "capability_sha256",
  "action_sha256",
  "model_sha256",
  "source_sha256",
]);
const forbiddenPlaintext = new Set([
  "claimed_actor",
  "actor_family",
  "runtime_family",
  "capability",
  "action",
  "model",
  "source",
  "content",
]);

function canonicalize(value) {
  if (Array.isArray(value)) {
    return value.map(canonicalize);
  }
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, canonicalize(value[key])]),
    );
  }
  return value;
}

function canonicalPayloadJson(payload) {
  return JSON.stringify(canonicalize(payload));
}

function computeReceiptHash(previousHash, payload) {
  return createHash("sha256")
    .update(`${previousHash}\n${canonicalPayloadJson(payload)}`, "utf8")
    .digest("hex");
}

function isStringArray(value) {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function validateReceipt(payload, sequence) {
  const errors = [];
  if (payload === null || typeof payload !== "object" || Array.isArray(payload)) {
    return [`receipt ${sequence}: payload must be an object`];
  }

  const fields = Object.keys(payload);
  const missing = [...requiredFields].filter((field) => !(field in payload)).sort();
  const extra = fields.filter((field) => !requiredFields.has(field)).sort();
  const plaintext = fields.filter((field) => forbiddenPlaintext.has(field)).sort();
  if (missing.length > 0) {
    errors.push(`receipt ${sequence}: missing fields: ${missing.join(", ")}`);
  }
  if (extra.length > 0) {
    errors.push(`receipt ${sequence}: unknown fields: ${extra.join(", ")}`);
  }
  if (plaintext.length > 0) {
    errors.push(
      `receipt ${sequence}: caller-controlled plaintext fields are forbidden: ${plaintext.join(", ")}`,
    );
  }

  if (payload.schema_version !== 2) {
    errors.push(`receipt ${sequence}: schema_version must equal 2`);
  }
  if (typeof payload.request_id !== "string" || payload.request_id.trim() === "") {
    errors.push(`receipt ${sequence}: request_id must be a non-empty string`);
  }
  if (typeof payload.allowed !== "boolean") {
    errors.push(`receipt ${sequence}: allowed must be a boolean`);
  }
  if (!new Set(["allow", "deny"]).has(payload.decision)) {
    errors.push(`receipt ${sequence}: decision must be allow or deny`);
  } else if (typeof payload.allowed === "boolean") {
    const expected = payload.allowed ? "allow" : "deny";
    if (payload.decision !== expected) {
      errors.push(
        `receipt ${sequence}: decision ${JSON.stringify(payload.decision)} conflicts with allowed=${payload.allowed}`,
      );
    }
  }
  if (!isStringArray(payload.reason_codes)) {
    errors.push(`receipt ${sequence}: reason_codes must be a string array`);
  }
  if (!isStringArray(payload.injection_matches)) {
    errors.push(`receipt ${sequence}: injection_matches must be a string array`);
  }
  for (const field of digestFields) {
    if (typeof payload[field] !== "string" || !digestPattern.test(payload[field])) {
      errors.push(`receipt ${sequence}: ${field} must be a lowercase SHA-256 hex digest`);
    }
  }
  return errors;
}

export function verifyVector(document) {
  const errors = [];
  if (document === null || typeof document !== "object" || Array.isArray(document)) {
    return {
      valid: false,
      receipts: 0,
      last_hash: "GENESIS",
      errors: ["vector document must be an object"],
    };
  }
  if (document.schema_version !== 1) {
    errors.push("vector schema_version must equal 1");
  }
  if (document.genesis !== "GENESIS") {
    errors.push("vector genesis must equal GENESIS");
  }
  if (!Array.isArray(document.receipts)) {
    return {
      valid: false,
      receipts: 0,
      last_hash: "GENESIS",
      errors: [...errors, "receipts must be an array"],
    };
  }

  let previousHash = "GENESIS";
  document.receipts.forEach((receipt, index) => {
    const expectedSequence = index + 1;
    if (receipt === null || typeof receipt !== "object" || Array.isArray(receipt)) {
      errors.push(`receipt ${expectedSequence}: vector entry must be an object`);
      return;
    }
    if (receipt.sequence !== expectedSequence) {
      errors.push(
        `receipt ${expectedSequence}: sequence must equal ${expectedSequence}, got ${JSON.stringify(receipt.sequence)}`,
      );
    }
    errors.push(...validateReceipt(receipt.payload, expectedSequence));
    if (receipt.previous_hash !== previousHash) {
      errors.push(`receipt ${expectedSequence}: previous_hash does not match prior receipt`);
    }
    const expectedHash = computeReceiptHash(previousHash, receipt.payload);
    if (receipt.receipt_hash !== expectedHash) {
      errors.push(`receipt ${expectedSequence}: receipt_hash mismatch`);
    }
    previousHash = expectedHash;
  });

  return {
    valid: errors.length === 0,
    receipts: document.receipts.length,
    last_hash: previousHash,
    errors,
  };
}

async function main() {
  const vectorPath = process.argv[2] ?? "spec/vectors/receipt-chain-v2.json";
  const document = JSON.parse(await readFile(vectorPath, "utf8"));
  const result = verifyVector(document);
  console.log(JSON.stringify(result, null, 2));
  process.exitCode = result.valid ? 0 : 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
