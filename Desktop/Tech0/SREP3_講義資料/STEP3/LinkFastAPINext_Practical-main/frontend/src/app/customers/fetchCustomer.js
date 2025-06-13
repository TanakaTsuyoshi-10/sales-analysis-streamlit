export default async function fetchCustomer(id = null) {
  const endpoint = process.env.NEXT_PUBLIC_API_ENDPOINT;

  if (!endpoint) {
    throw new Error("環境変数 NEXT_PUBLIC_API_ENDPOINT が設定されていません");
  }

  const url = id
    ? `${endpoint}/customers?customer_id=${id}`
    : `${endpoint}/allcustomers`;

  const res = await fetch(url, { cache: "no-cache" });

  if (!res.ok) {
    throw new Error("Failed to fetch customer(s)");
  }

  return res.json(); // 常に配列で返す
}