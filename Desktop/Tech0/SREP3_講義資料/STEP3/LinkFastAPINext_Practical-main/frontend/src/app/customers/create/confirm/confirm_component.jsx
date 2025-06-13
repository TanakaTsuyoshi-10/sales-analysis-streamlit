"use client";

import { useSearchParams, useRouter } from "next/navigation";
import OneCustomerInfoCard from "@/app/components/one_customer_info_card.jsx";
import fetchCustomer from "./fetchCustomer";
import { useEffect, useState } from "react";

export default function ConfirmPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const customer_id = searchParams.get("customer_id");
  const [customer, setCustomer] = useState(null);

  useEffect(() => {
    if (customer_id) {
      fetchCustomer(customer_id).then((data) => {
        setCustomer(data[0]);
      });
    }
  }, [customer_id]);

  if (!customer) return <div>Loading...</div>;

  return (
    <div className="card bordered bg-white border-blue-200 border-2 max-w-sm m-4">
      <div className="alert alert-success p-4 text-center">正常に作成しました</div>
      <OneCustomerInfoCard {...customer} />
      <button onClick={() => router.push("/customers")}>
        <div className="btn btn-primary m-4 text-2xl">戻る</div>
      </button>
    </div>
  );
}