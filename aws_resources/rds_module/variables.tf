variable "db_user" {
  type        = string
}

variable "db_password" {
  type        = string
  sensitive   = true
}

variable "db_name"{
    type = string
}

variable "security_group"{
    type = string
}

variable  "subnet_group"{
    type = string
}