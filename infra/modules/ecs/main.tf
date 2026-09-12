variable "name" { type = string }
variable "region" { type = string }
variable "image_uri" { type = string }
variable "enable_inference" { type = bool }
variable "target_group_arn" { type = string }
variable "subnet_ids" { type = list(string) }
variable "security_group_id" { type = string }
variable "execution_role" { type = string }
variable "inference_role" { type = string }
variable "training_role" { type = string }
variable "model_bucket" { type = string }
variable "datasets_bucket" { type = string }
variable "model_key" { type = string }
variable "use_onnx" { type = bool }
variable "training_command" { type = list(string) }
variable "log_group" { type = string }

locals {
  logs = {
    logDriver = "awslogs"
    options = {
      awslogs-group         = var.log_group
      awslogs-region        = var.region
      awslogs-stream-prefix = "ecs"
    }
  }
}
resource "aws_ecs_cluster" "this" {
  name = var.name
  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}
resource "aws_ecs_task_definition" "inference" {
  family                   = "${var.name}-inference"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = var.execution_role
  task_role_arn            = var.inference_role
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  container_definitions = jsonencode([{
    name         = "api", image = var.image_uri, essential = true, user = "10001"
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    environment = [
      { name = "MODEL_BUCKET", value = var.model_bucket },
      { name = "MODEL_KEY", value = var.model_key },
      { name = "USE_ONNX", value = tostring(var.use_onnx) },
      { name = "AWS_REGION", value = var.region }
    ]
    logConfiguration = local.logs
    healthCheck = {
      command  = ["CMD", "python", "-c", "import json,urllib.request; r=json.load(urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3)); assert r['model']=='loaded'"]
      interval = 15, timeout = 5, retries = 3, startPeriod = 60
    }
  }])
}
resource "aws_ecs_task_definition" "training" {
  family                   = "${var.name}-training"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = var.execution_role
  task_role_arn            = var.training_role
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  container_definitions = jsonencode([{
    name    = "train", image = var.image_uri, essential = true, user = "10001"
    command = var.training_command
    environment = [
      { name = "DATA_BUCKET", value = var.datasets_bucket },
      { name = "DATA_KEY", value = "processed/train.csv" },
      { name = "MODEL_BUCKET", value = var.model_bucket },
      { name = "MODEL_KEY", value = "models/model.pkl" },
      { name = "AWS_REGION", value = var.region }
    ]
    logConfiguration = local.logs
  }])
}
resource "aws_ecs_service" "this" {
  count                              = var.enable_inference ? 1 : 0
  name                               = var.name
  cluster                            = aws_ecs_cluster.this.id
  task_definition                    = aws_ecs_task_definition.inference.arn
  desired_count                      = 1
  launch_type                        = "FARGATE"
  health_check_grace_period_seconds  = 90
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  wait_for_steady_state              = true
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [var.security_group_id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "api"
    container_port   = 8000
  }
}
output "cluster_name" { value = aws_ecs_cluster.this.name }
output "training_task_definition" { value = aws_ecs_task_definition.training.arn }
output "inference_task_definition" { value = aws_ecs_task_definition.inference.arn }
