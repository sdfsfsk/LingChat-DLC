fn main() {
    println!("cargo:rustc-check-cfg=cfg(desktop)");
    println!("cargo:rustc-check-cfg=cfg(mobile)");
    let target = std::env::var("CARGO_CFG_TARGET_OS").unwrap();
    println!(
        "cargo:rustc-cfg={}",
        if target == "android" || target == "ios" {
            "mobile"
        } else {
            "desktop"
        }
    );
}
