//! Approval-gated remote control for Creator Extend.

use relay_client::control::{RemoteRuntime, RemoteRuntimeView, RemoteSettings};
use serde_json::json;
use std::sync::{Arc, Mutex};

use crate::AppConfig;

pub struct CreatorRemoteControl {
    runtime: RemoteRuntime,
    app_config: Arc<Mutex<AppConfig>>,
}

impl CreatorRemoteControl {
    pub fn new(app_config: Arc<Mutex<AppConfig>>) -> Self {
        Self {
            runtime: RemoteRuntime::new(relay_client::Product::CreatorExtend),
            app_config,
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
                ("comfyui", "queue_workflow") => {
                    let path = payload["workflow_path"]
                        .as_str()
                        .ok_or("Workflow path is missing")?;
                    let workflow = crate::comfyui::load_workflow_json(path)
                        .map_err(|error| error.to_string())?;
                    let url = self.app_config.lock().unwrap().comfyui_url.clone();
                    crate::comfyui::require_compatible_workflow(&url, &workflow)
                        .await
                        .map_err(|error| error.to_string())?;
                    let prompt_id = crate::comfyui::queue_prompt(&url, &workflow)
                        .await
                        .map_err(|error| error.to_string())?;
                    json!({"prompt_id": prompt_id})
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
}
