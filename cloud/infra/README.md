# Terraform (planned A1 resources)

This directory declares only the minimal R2 bucket and Queue that A1 will need.
Run `terraform init -backend=false` and `terraform validate` offline. CI supplies
`account_id`, `environment`, and the token through secrets; no token belongs here.
State uses the local backend for now. Move it to a locked R2 backend before shared
production operation.
