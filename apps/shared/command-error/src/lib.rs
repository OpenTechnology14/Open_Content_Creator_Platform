//! A stable, structured error envelope for Tauri commands.
//!
//! Both apps' commands used to `.map_err(|e| e.to_string())`, returning a
//! bare string the frontend could only log, never branch on (was it a
//! timeout? worth retrying? a bad input?). Tauri 2 commands accept any
//! `Serialize` type as the `Err` variant, not just `String`, so this
//! replaces the string with a real, typed shape both apps' frontends can
//! render and reason about consistently.
//!
//! Matches `PROPOSAL_RELEASE_GAP_CLOSURE.md` §7.1's own example envelope
//! (`{"error": {"code", "message", "retryable", "operation_id", "details"}}`).

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ErrorCode {
    /// A call timed out — never a guessed/default value in its place.
    RequestTimeout,
    /// The remote service (OBS, ComfyUI) could not be reached at all.
    DependencyUnreachable,
    /// The dependency reached, but rejected the request as malformed.
    InvalidRequest,
    /// A named resource (a workflow file, a scene) does not exist.
    NotFound,
    /// A path resolved outside its allowed directory — refused, not served.
    PathEscape,
    /// Anything that doesn't fit a more specific code above.
    Internal,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorEnvelope {
    pub code: ErrorCode,
    pub message: String,
    /// Whether the same call is expected to succeed if retried unchanged
    /// (e.g. a timeout) versus needing a different input (e.g. not found).
    pub retryable: bool,
    /// Correlates a frontend-visible error with backend logs for the same
    /// call, when the caller supplies one — not required.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub operation_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub details: Option<serde_json::Value>,
}

impl ErrorEnvelope {
    pub fn new(code: ErrorCode, message: impl Into<String>) -> Self {
        let retryable = matches!(code, ErrorCode::RequestTimeout | ErrorCode::DependencyUnreachable);
        Self { code, message: message.into(), retryable, operation_id: None, details: None }
    }

    pub fn timeout(message: impl Into<String>) -> Self {
        Self::new(ErrorCode::RequestTimeout, message)
    }

    pub fn dependency_unreachable(message: impl Into<String>) -> Self {
        Self::new(ErrorCode::DependencyUnreachable, message)
    }

    pub fn invalid_request(message: impl Into<String>) -> Self {
        Self::new(ErrorCode::InvalidRequest, message)
    }

    pub fn not_found(message: impl Into<String>) -> Self {
        Self::new(ErrorCode::NotFound, message)
    }

    pub fn path_escape(message: impl Into<String>) -> Self {
        Self::new(ErrorCode::PathEscape, message)
    }

    pub fn internal(message: impl Into<String>) -> Self {
        Self::new(ErrorCode::Internal, message)
    }

    pub fn with_operation_id(mut self, id: impl Into<String>) -> Self {
        self.operation_id = Some(id.into());
        self
    }
}

impl std::fmt::Display for ErrorEnvelope {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}: {}", self.code, self.message)
    }
}

impl std::error::Error for ErrorEnvelope {}
