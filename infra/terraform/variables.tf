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

variable "llm_base_url" {
  type        = string
  description = "OpenAI-compatible Emberlane endpoint URL, for example https://example.com/v1"
}

variable "llm_api_key" {
  type        = string
  sensitive   = true
  description = "API key for the Emberlane OpenAI-compatible endpoint."
}

variable "llm_model" {
  type        = string
  default     = "qwen35_9b_awq"
  description = "Emberlane model profile for cloud summaries."
}
