export interface Summary {
  headline: string;
  headline_ratio: number;
  b2b: {
    invoiced: number;
    gross_payments: number;
    net_received: number;
    total_deductions: number;
    deduction_count: number;
    recovered: number;
    leakage_pct: number;
    remittance_count: number;
  };
  dtc: {
    gross: number;
    processing_fees: number;
    refunds: number;
    chargebacks_lost: number;
    net_received: number;
    leakage_pct: number;
  };
  combined: {
    total_invoiced: number;
    total_net: number;
    total_leakage: number;
    cents_per_dollar: number;
  };
  meta: {
    retailers_b2b: number;
    orders_b2b: number;
    orders_dtc: number;
    skus: number;
    time_window: string;
  };
}

export interface DeductionStage {
  stage: string;
  label: string;
  amount: number;
  count?: number;
  recovered?: number;
}

export interface Lifecycle {
  b2b: {
    gross: number;
    net: number;
    stages: DeductionStage[];
  };
  dtc: {
    gross: number;
    net: number;
    stages: DeductionStage[];
  };
}

export interface RetailerLeakage {
  name: string;
  gross: number;
  net: number;
  leakage: number;
  leakage_pct: number;
  remittances: number;
}

export interface RetailerTimeToCash {
  name: string;
  avg_days: number;
  median_days: number;
  sample_size: number;
}

export interface RetailerTimeToCashMeta {
  covered_orders: number;
  total_orders: number;
  coverage_pct: number;
}

export interface Retailers {
  leakage: RetailerLeakage[];
  time_to_cash: RetailerTimeToCash[];
  time_to_cash_meta: RetailerTimeToCashMeta;
}
