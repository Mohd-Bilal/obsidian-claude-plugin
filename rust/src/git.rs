use std::path::Path;
use std::process::Command;
use tokio::time::{sleep, Duration};

/// Run a git command in the given directory. Returns the exit status.
fn run_git(vault_root: &Path, args: &[&str]) -> std::io::Result<std::process::ExitStatus> {
    Command::new("git")
        .args(args)
        .current_dir(vault_root)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
}

/// Ensure vault_root is a git repository; `git init` if needed and write a
/// default .gitignore that excludes Obsidian workspace/cache files.
pub fn ensure_git_repo(vault_root: &Path) {
    if vault_root.join(".git").exists() {
        return;
    }
    let _ = run_git(vault_root, &["init"]);
    let gitignore = vault_root.join(".gitignore");
    if !gitignore.exists() {
        let _ = std::fs::write(gitignore, ".obsidian/workspace*\n.obsidian/cache\n");
    }
}

/// Stage all changes and commit. Returns true if a commit was actually made
/// (i.e. there were staged changes).
pub fn commit_all(vault_root: &Path, message: &str) -> bool {
    let _ = run_git(vault_root, &["add", "-A"]);
    run_git(vault_root, &["commit", "-m", message])
        .map(|s| s.success())
        .unwrap_or(false)
}

/// Periodically commit all changes in the vault. This is intended to be
/// spawned as a `tokio::task` and cancelled via the task handle on shutdown.
pub async fn auto_commit_loop(vault_root: std::path::PathBuf, interval_seconds: u64) {
    let interval = Duration::from_secs(interval_seconds);
    loop {
        sleep(interval).await;
        // Run the blocking git commands on the thread-pool so we never block
        // the async runtime.
        let root = vault_root.clone();
        tokio::task::spawn_blocking(move || {
            commit_all(&root, "obsidian-mcp: auto-commit");
        })
        .await
        .ok();
    }
}
