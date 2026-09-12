variable "home_ip_address" {
  description = "home_ip_address"
  type        = string
}

variable "vpc_id" {
  description = "vpc_id"
  type        = string
}

variable "db_password" {
  description = "Mot de passe RDS PostgreSQL"
  type        = string
  sensitive   = true
}

variable "secondary_subnet_id" {
  description = "Subnet secondaire pour le subnet group RDS (AZ différente de eu-west-3c)"
  type        = string
}