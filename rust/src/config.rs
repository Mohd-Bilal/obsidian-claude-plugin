use std::path::PathBuf;
use std::env;

/// Configuration loaded from environment variables.
#[derive(Debug, Clone)]
pub struct Config {
    /// Explicit vault path; None means use vault discovery.
    pub vault_path: Option<PathBuf>,
    /// Auto-commit interval in seconds; None means disabled.
    /// Stored for future use; the Rust port does not currently run a background git loop.
    #[allow(dead_code)]
    pub git_autocommit_interval: Option<u64>,
    /// Name of the templates folder inside the vault.
    pub templates_folder: String,
}

/// Parse an interval string like "15m", "1h", "300s", "300" into seconds.
fn parse_interval(raw: &str) -> Option<u64> {
    let raw = raw.trim();
    if raw.is_empty() {
        return None;
    }
    // Try to split a trailing unit character
    let (digits, unit) = if raw.ends_with(|c: char| c.is_alphabetic()) {
        let (d, u) = raw.split_at(raw.len() - 1);
        (d, u)
    } else {
        (raw, "s")
    };
    let value: u64 = digits.parse().ok()?;
    let multiplier = match unit.to_ascii_lowercase().as_str() {
        "s" => 1,
        "m" => 60,
        "h" => 3600,
        _ => return None,
    };
    Some(value * multiplier)
}

/// Load configuration from environment variables.
pub fn load_config() -> Config {
    let vault_path = env::var("OBSIDIAN_VAULT_PATH")
        .ok()
        .filter(|s| !s.is_empty())
        .map(PathBuf::from);

    let git_autocommit_interval = env::var("GIT_AUTOCOMMIT_INTERVAL")
        .ok()
        .and_then(|s| parse_interval(&s));

    let templates_folder = env::var("OBSIDIAN_TEMPLATES_FOLDER")
        .unwrap_or_else(|_| "Templates".to_string());

    Config {
        vault_path,
        git_autocommit_interval,
        templates_folder,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_interval() {
        assert_eq!(parse_interval("300"), Some(300));
        assert_eq!(parse_interval("300s"), Some(300));
        assert_eq!(parse_interval("15m"), Some(900));
        assert_eq!(parse_interval("1h"), Some(3600));
        assert_eq!(parse_interval(""), None);
    }
}
