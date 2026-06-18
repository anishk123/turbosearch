variable "project" {
  type    = string
  default = "turbosearch"
}

variable "region" {
  type    = string
  default = "us-west-2"
}

variable "db_name" {
  type    = string
  default = "turbosearch"
}

variable "db_username" {
  type    = string
  default = "turbosearch"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "instance_type" {
  type    = string
  default = "t3.small"
}

variable "allowed_http_cidr" {
  type    = string
  default = "0.0.0.0/0"
}

