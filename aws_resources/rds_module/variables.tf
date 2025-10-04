variable "db_password" {
  type      = string
  sensitive = true
}

variable "security_group" {
  type = string
}

variable "subnet_group" {
  type = string
}
