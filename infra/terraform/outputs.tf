output "app_url" {
  value = "http://${aws_instance.app.public_ip}:8000"
}

output "aurora_endpoint" {
  value = aws_rds_cluster.main.endpoint
}

