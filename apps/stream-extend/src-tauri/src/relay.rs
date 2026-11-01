//! Approval-gated remote control for Stream Extend.

use relay_client::control::{RemoteRuntime, RemoteRuntimeView, RemoteSettings};
use serde_json::json;
use std::sync::{Arc, Mutex};

use crate::{obs, AppConfig};

pub struct StreamRemoteControl {
    runtime: RemoteRuntime,
    app_config: Arc<Mutex<AppConfig>>,
    obs_cache: Arc<obs::ObsClientCache>,
}

impl StreamRemoteControl {
    pub fn new(app_config: Arc<Mutex<AppConfig>>, obs_cache: Arc<obs::ObsClientCache>) -> Self {
        Self {
            runtime: RemoteRuntime::new(relay_client::Product::StreamExtend),
            app_config,
            obs_cache,
        }
    }

    pub async fn connect(&self, settings: &RemoteSettings) -> Result<(), String> {
        self.runtime.connect(settings).await
    }
    pub async fn disconnect(&self) {
        self.runtime.disconnect().await;
    }
    pub async fn status(&self) -> RemoteRuntimeView {
        self.runtime.view().await
    }
    pub async fn deny(&self, id: &str) -> Result<(), String> {
        self.runtime.deny(id).await
    }

    pub async fn request(
        &self,
        target_device_id: String,
        target: String,
        action: String,
        payload: serde_json::Value,
    ) -> Result<String, String> {
        self.runtime
            .request(target_device_id, target, action, payload)
            .await
    }

    pub async fn approve(&self, id: &str) -> Result<serde_json::Value, String> {
        let (command, payload) = self.runtime.take_for_approval(id).await?;
        let execution: Result<serde_json::Value, String> = async {
            Ok(match (command.target.as_str(), command.action.as_str()) {
                ("obs", "switch_scene") => {
                    let scene = payload["scene"].as_str().ok_or("Scene is missing")?;
                    let (host, port, password) = self.obs_connection();
                    let scenes =
                        obs::switch_scene(&self.obs_cache, &host, port, password.as_deref(), scene)
                            .await
                            .map_err(|error| error.to_string())?;
                    json!({"current_scene": scene, "observed_scene_count": scenes.len()})
                }
                ("obs", "toggle_stream") => {
                    let (host, port, password) = self.obs_connection();
                    let active =
                        obs::toggle_stream(&self.obs_cache, &host, port, password.as_deref())
                            .await
                            .map_err(|error| error.to_string())?;
                    json!({"stream_active": active})
                }
                _ => return Err("Remote action is not implemented".into()),
            })
        }
        .await;
        match execution {
            Ok(result) => {
                self.runtime
                    .complete(&command.id, true, result.clone())
                    .await?;
                Ok(result)
            }
            Err(error) => {
                let _ = self
                    .runtime
                    .complete(
                        &command.id,
                        false,
                        json!({"error": "Action failed on the creator device"}),
                    )
                    .await;
                Err(error)
            }
        }
    }

    fn obs_connection(&self) -> (String, u16, Option<String>) {
        let config = self.app_config.lock().unwrap();
        (
            config.obs_host.clone(),
            config.obs_port,
            config.obs_password.clone(),
        )
    }
}
