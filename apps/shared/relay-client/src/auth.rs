//! Authentication helpers for relay client.
//!
//! Handles JWT token management for hosted relay,
//! and API key auth for self-hosted relay.

use crate::RelayError;
use serde::{Deserialize, Serialize};

/// JWT claims for hosted relay authentication.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RelayClaims {
    /// Tenant ID (unique per subscriber).
    pub tenant_id: String,
    /// Subscription tier.
    pub tier: String,
    /// Device ID.
    pub device_id: String,
    /// Issued at (Unix timestamp).
    pub iat: u64,
    /// Expires at (Unix timestamp).
    pub exp: u64,
    /// Issuer — "streamextend.com" or "creatorextend.com".
    pub iss: String,
}

/// Verify an app store receipt and exchange it for a relay JWT.
///
/// This calls the hosted relay's `/api/v1/auth/verify-purchase` endpoint.
/// The relay validates the receipt with Apple/Google/Microsoft, provisions
/// a tenant if new, and returns a JWT.
pub async fn verify_app_store_purchase(
    api_url: &str,
    receipt: &str,
    store: &str, // "apple", "google", "microsoft"
) -> Result<String, RelayError> {
    let client = reqwest::Client::new();
    let response = client
        .post(format!("{}/auth/verify-purchase", api_url))
        .json(&serde_json::json!({
            "receipt": receipt,
            "store": store,
        }))
        .send()
        .await
        .map_err(|e| RelayError::Connection(e.to_string()))?;

    if !response.status().is_success() {
        let error_text = response.text().await.unwrap_or_default();
        return Err(RelayError::AuthFailed(format!(
            "Purchase verification failed: {}",
            error_text
        )));
    }

    #[derive(Deserialize)]
    struct VerifyResponse {
        jwt: String,
    }

    let body: VerifyResponse = response
        .json()
        .await
        .map_err(|e| RelayError::Connection(e.to_string()))?;

    Ok(body.jwt)
}

/// Refresh an existing JWT before it expires.
pub async fn refresh_jwt(api_url: &str, current_jwt: &str) -> Result<String, RelayError> {
    let client = reqwest::Client::new();
    let response = client
        .post(format!("{}/auth/refresh", api_url))
        .bearer_auth(current_jwt)
        .send()
        .await
        .map_err(|e| RelayError::Connection(e.to_string()))?;

    if !response.status().is_success() {
        return Err(RelayError::AuthFailed("Token refresh failed".into()));
    }

    #[derive(Deserialize)]
    struct RefreshResponse {
        jwt: String,
    }

    let body: RefreshResponse = response
        .json()
        .await
        .map_err(|e| RelayError::Connection(e.to_string()))?;

    Ok(body.jwt)
}

/// Validate a self-hosted relay URL by hitting its health endpoint.
pub async fn validate_self_hosted(url: &str, api_key: Option<&str>) -> Result<(), RelayError> {
    let normalized = url.trim_end_matches('/');
    let health_url = format!("{}/api/v1/health", normalized);

    let client = reqwest::Client::new();
    let mut request = client.get(&health_url);

    if let Some(key) = api_key {
        request = request.bearer_auth(key);
    }

    let response = request
        .timeout(std::time::Duration::from_secs(5))
        .send()
        .await
        .map_err(|e| RelayError::Connection(format!("Cannot reach relay at {}: {}", url, e)))?;

    if !response.status().is_success() {
        return Err(RelayError::Connection(format!(
            "Relay at {} returned status {}",
            url,
            response.status()
        )));
    }

    Ok(())
}
