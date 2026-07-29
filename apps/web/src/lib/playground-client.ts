export interface EntitySpan {
  entityType: string;
  start: number;
  end: number;
  score: number;
}

export interface ProtectResult {
  maskedText: string;
  requestId: string;
  entities?: EntitySpan[] | null;
}

export const ENTITY_TYPES: { code: string; label: string }[] = [
  { code: "PERSON", label: "氏名" },
  { code: "PHONE_NUMBER", label: "電話番号" },
  { code: "EMAIL_ADDRESS", label: "メール" },
  { code: "LOCATION", label: "住所" },
  { code: "JP_POSTAL_CODE", label: "郵便番号" },
  { code: "URL", label: "URL" },
  { code: "IP_ADDRESS", label: "IP" },
  { code: "JP_BANK_ACCOUNT", label: "銀行口座" },
  { code: "CREDIT_CARD", label: "クレジットカード" },
  { code: "JP_MYNUMBER", label: "マイナンバー" },
  { code: "JP_PASSPORT", label: "パスポート" },
  { code: "JP_CORPORATE_NUMBER", label: "法人番号" },
];

export async function runProtect(
  text: string,
  rules: Record<string, boolean>,
): Promise<ProtectResult> {
  const res = await fetch("/api/playground/protect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, rules }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? `Request failed (${res.status})`);
  }
  return res.json();
}
