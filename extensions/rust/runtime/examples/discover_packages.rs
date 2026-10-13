//! Live read-only release discovery; downloads manifests, never package archives.
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let catalog = ling_chat_dlc_runtime::games::discovery::discover().await?;
    println!("{}", serde_json::to_string_pretty(&catalog)?);
    Ok(())
}
