variable "region" {
  type    = string
  default = "us-east-1"
}
variable "name" {
  type    = string
  default = "tc03-triagem"
}
variable "expires_on" {
  type    = string
  default = "2026-09-26"
}
variable "image_uri" {
  description = "URI ECR com tag imutável ou digest; mesma imagem para treino e inferência."
  type        = string
}
variable "enable_inference" {
  description = "Ativar somente com artefato real disponível no S3."
  type        = bool
  default     = false
}
variable "model_key" {
  type    = string
  default = "models/model.pkl"
}
variable "use_onnx" {
  type    = bool
  default = false
}
variable "training_command" {
  description = "Contrato inicial: Dev C implementará ingestão S3/upload na DAG ou wrapper."
  type        = list(string)
  default     = ["python", "-m", "src.train", "--data", "/app/data/processed/train.csv", "--model", "/app/models/model.pkl", "--classifier", "logistic"]
}
