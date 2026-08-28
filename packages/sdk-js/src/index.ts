/**
 * SecureAI Studio SDK — a thin, typed wrapper over the REST API.
 *
 *   import { SecureAI } from "@secureai/sdk";
 *   const client = new SecureAI(process.env.SECUREAI_PROTECT_KEY!);
 *   const { maskedText } = await client.protect("田中太郎 090-1234-5678");
 */

export interface Entity {
  entityType: string;
  start: number;
  end: number;
  score: number;
}

export interface ProtectResult {
  maskedText: string;
  requestId: string;
  entities?: Entity[] | null;
}

export interface DetectResult {
  entities: Entity[];
  entityCounts: Record<string, number>;
  requestId: string;
}

export interface AnalyzeResult {
  analysis: string;
  requestId: string;
  usage: { inputTokens: number; outputTokens: number };
}

export interface ProtectOptions {
  returnEntities?: boolean;
  rules?: Record<string, boolean> | null;
}

export interface AnalyzeOptions {
  providerId?: string | null;
  model?: string | null;
  deanonymize?: boolean;
}

export class SecureAIError extends Error {
  code: string;
  status?: number;
  requestId?: string;
  constructor(
    message: string,
    opts: { code?: string; status?: number; requestId?: string } = {},
  ) {
    super(message);
    this.name = "SecureAIError";
    this.code = opts.code ?? "ERROR";
    this.status = opts.status;
    this.requestId = opts.requestId;
  }
}

export interface SecureAIOptions {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
}

const DEFAULT_BASE_URL = "https://api.secureai.studio";

export class SecureAI {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof fetch;

  constructor(apiKey: string, opts: SecureAIOptions = {}) {
    if (!apiKey) throw new Error("apiKey is required");
    this.apiKey = apiKey;
    this.baseUrl = (opts.baseUrl ?? DEFAULT_BASE_URL).replace(/\/$/, "");
    this.fetchImpl = opts.fetchImpl ?? fetch;
  }

  protect(text: string, options: ProtectOptions = {}): Promise<ProtectResult> {
    return this.post<ProtectResult>("/v1/protect", {
      text,
      options: { returnEntities: options.returnEntities ?? false, rules: options.rules ?? null },
    });
  }

  detect(text: string, options: { rules?: Record<string, boolean> | null } = {}): Promise<DetectResult> {
    return this.post<DetectResult>("/v1/detect", { text, options: { rules: options.rules ?? null } });
  }

  analyze(text: string, options: AnalyzeOptions = {}): Promise<AnalyzeResult> {
    return this.post<AnalyzeResult>("/v1/analyze", {
      text,
      options: {
        providerId: options.providerId ?? null,
        model: options.model ?? null,
        deanonymize: options.deanonymize ?? false,
      },
    });
  }

  private async post<T>(path: string, body: unknown): Promise<T> {
    const res = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${this.apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      let err: { code?: string; message?: string; requestId?: string } = {};
      try {
        err = ((await res.json()) as { error?: typeof err }).error ?? {};
      } catch {
        /* ignore parse errors */
      }
      throw new SecureAIError(err.message ?? `Request failed (${res.status})`, {
        code: err.code ?? "ERROR",
        status: res.status,
        requestId: err.requestId,
      });
    }
    return (await res.json()) as T;
  }
}
