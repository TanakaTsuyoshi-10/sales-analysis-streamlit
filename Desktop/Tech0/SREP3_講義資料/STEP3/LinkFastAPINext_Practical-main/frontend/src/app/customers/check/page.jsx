// /src/app/customers/check/page.jsx
"use client";

import { Suspense } from "react";
import CheckPageClient from "./CheckPageClient";

export default function CheckPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <CheckPageClient />
    </Suspense>
  );
}