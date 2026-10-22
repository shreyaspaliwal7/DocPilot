from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  gemini_api_key: str = ""
  gemini_chat_model: str = "gemini-2.5-flash"
  gemini_fallback_model: str = "gemini-2.5-flash-lite"
  gemini_embed_model: str = "gemini-embedding-001"
  embedding_dim: int = 768
  requests_per_minute: int = 15
  max_retries: int = 3
  database_url: str = "postgresql://postgres:postgres@postgres:5432/docpilot"
  readonly_database_url: str = (
      "postgresql://readonly_user:readonly_pass@postgres:5432/docpilot"
  )
  chunk_size: int = 800
  chunk_overlap: int = 100
  top_k: int = 4
  score_threshold: float = 0.50
  max_file_size_mb: int = 10
  batch_embed_size: int = 20
  exchange_api_url: str = "https://api.frankfurter.dev"
  sql_row_limit: int = 50
  sql_timeout_seconds: int = 5
  max_tool_steps: int = 3
  cost_per_1k_input: float = 0.0
  cost_per_1k_output: float = 0.0
  eval_api_url: str = "http://localhost:8000"
  eval_delay_seconds: float = 2.0

  model_config = SettingsConfigDict(
      env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
  )


settings = Settings()
