// /src/app/customers/create/confirm/page.jsx
"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

export default function ConfirmPageWrapper() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ConfirmPage />
    </Suspense>
  );
}

function ConfirmPage() {
  const searchParams = useSearchParams();
  const name = searchParams.get("name");
  const age = searchParams.get("age");
  const gender = searchParams.get("gender");

  return (
    <div className="p-4">
      <div className="alert alert-success mb-4">新規登録が完了しました</div>
      <div className="card bordered bg-white border-blue-200 border-2 max-w-sm m-4">
        <div className="card-body">
          <h2 className="card-title">顧客情報</h2>
          <p>名前: {name}</p>
          <p>年齢: {age}</p>
          <p>性別: {gender}</p>
        </div>
      </div>
      <a href="/customers">
        <button className="btn btn-outline btn-accent">一覧に戻る</button>
      </a>
    </div>
  );
}