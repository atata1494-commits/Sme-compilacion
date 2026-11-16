import { DatabaseSync } from 'node:sqlite';
import { mkdirSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const directory = mkdtempSync(join(tmpdir(), 'sme-sync-sqlite-'));
let nextDatabase = 0;
export const databasePaths = [];
const reusablePaths = [];
export function reuseDatabasePath(path) { reusablePaths.push(path); }

class TestConnection {
  constructor(path) {
    this.path = path;
    this.db = new DatabaseSync(path);
    this.opened = false;
  }
  async isDBOpen() { return { result: this.opened }; }
  async open() { this.opened = true; return { result: true }; }
  async execute(sql) { this.db.exec(sql); return { changes: { changes: 0 } }; }
  async query(sql, values = []) {
    const statement = this.db.prepare(sql);
    return { values: values.length ? statement.all(...values) : statement.all() };
  }
  async run(sql, values = []) {
    const result = this.db.prepare(sql).run(...values);
    return { changes: { changes: Number(result.changes) } };
  }
  async beginTransaction() { this.db.exec('BEGIN IMMEDIATE'); }
  async commitTransaction() { this.db.exec('COMMIT'); }
  async rollbackTransaction() { this.db.exec('ROLLBACK'); }
  async close() { if (this.opened) this.db.close(); this.opened = false; }
}

export class SQLiteConnection {
  constructor() { this.connection = null; }
  async checkConnectionsConsistency() { return { result: true }; }
  async isConnection() { return { result: false }; }
  async createConnection() {
    const path = reusablePaths.shift() || join(directory, `device-${nextDatabase++}.sqlite`);
    databasePaths.push(path);
    this.connection = new TestConnection(path);
    return this.connection;
  }
  async retrieveConnection() { return this.connection; }
  async closeConnection() { if (this.connection) await this.connection.close(); }
}

export const CapacitorSQLite = {};
export function cleanupTestDatabases() {
  rmSync(directory, { recursive: true, force: true });
  mkdirSync(directory, { recursive: true });
}
