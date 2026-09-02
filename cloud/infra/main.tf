resource "cloudflare_r2_bucket" "artifacts" {
  account_id = var.account_id
  name       = "rvw-artifacts-${var.environment}"
  location   = "enam"
  # Planned A1 artifact persistence target; not consumed by Worker code yet.
}

resource "cloudflare_queue" "review_jobs" {
  account_id = var.account_id
  queue_name = "rvw-review-jobs-${var.environment}"
  # Planned A1 webhook-to-Sandbox job transport; not consumed yet.
}
