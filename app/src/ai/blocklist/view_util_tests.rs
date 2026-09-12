use warp_core::features::FeatureFlag;

use super::*;
use crate::settings::UsageDisplayUnit;

#[test]
fn format_usage_returns_credits_only_when_flag_disabled() {
    let _flag = FeatureFlag::PricingTransparency.override_enabled(false);

    assert_eq!(
        format_usage(20.0, Some(12345), Some(36.0), UsageDisplayUnit::Dollars),
        format_credits(20.0)
    );
}

#[test]
fn format_usage_uses_credits_unit() {
    let _flag = FeatureFlag::PricingTransparency.override_enabled(true);

    assert_eq!(
        format_usage(20.0, Some(12345), Some(36.0), UsageDisplayUnit::Credits),
        "12,345 tokens / 20 créditos"
    );
}

#[test]
fn format_usage_uses_dollars_unit() {
    let _flag = FeatureFlag::PricingTransparency.override_enabled(true);

    assert_eq!(
        format_usage(20.0, Some(12345), Some(36.0), UsageDisplayUnit::Dollars),
        "12,345 tokens / $0.36"
    );
}

#[test]
fn format_usage_formats_large_token_counts_with_thousands_separators() {
    let _flag = FeatureFlag::PricingTransparency.override_enabled(true);

    assert_eq!(
        format_usage(26.9, Some(719_124), Some(48.0), UsageDisplayUnit::Dollars),
        "719,124 tokens / $0.48"
    );
}

#[test]
fn format_usage_falls_back_to_credits_when_dollars_unavailable() {
    let _flag = FeatureFlag::PricingTransparency.override_enabled(true);

    assert_eq!(
        format_usage(20.0, Some(12345), None, UsageDisplayUnit::Dollars),
        format_credits(20.0)
    );
}

#[test]
fn format_usage_omits_tokens_when_tokens_is_unknown() {
    let _flag = FeatureFlag::PricingTransparency.override_enabled(true);

    assert_eq!(
        format_usage(20.0, None, Some(36.0), UsageDisplayUnit::Dollars),
        "$0.36"
    );
    assert_eq!(
        format_usage(20.0, None, Some(36.0), UsageDisplayUnit::Credits),
        format_credits(20.0)
    );
}

#[test]
fn format_usage_omits_tokens_when_tokens_is_zero() {
    let _flag = FeatureFlag::PricingTransparency.override_enabled(true);

    assert_eq!(
        format_usage(20.0, Some(0), Some(36.0), UsageDisplayUnit::Dollars),
        "$0.36"
    );
}

#[test]
fn format_usage_credits_unit_omits_tokens_when_tokens_is_zero() {
    let _flag = FeatureFlag::PricingTransparency.override_enabled(true);

    assert_eq!(
        format_usage(20.0, Some(0), None, UsageDisplayUnit::Credits),
        format_credits(20.0)
    );
}

#[test]
fn usage_label_uses_dollars_wording_when_unit_is_dollars_and_flag_enabled() {
    let _flag = FeatureFlag::PricingTransparency.override_enabled(true);

    assert_eq!(
        usage_label(UsageLabelKind::Plain, Some(36.0), UsageDisplayUnit::Dollars),
        "Uso cobrado"
    );
    assert_eq!(
        usage_label(
            UsageLabelKind::LastResponse,
            Some(36.0),
            UsageDisplayUnit::Dollars
        ),
        "Uso cobrado (última respuesta)"
    );
    assert_eq!(
        usage_label(UsageLabelKind::Total, Some(36.0), UsageDisplayUnit::Dollars),
        "Uso cobrado (total)"
    );
    assert_eq!(
        usage_label(
            UsageLabelKind::DetailsPanel,
            Some(36.0),
            UsageDisplayUnit::Dollars
        ),
        "Uso"
    );
}

#[test]
fn usage_label_uses_credits_wording_when_unit_is_credits() {
    let _flag = FeatureFlag::PricingTransparency.override_enabled(true);

    assert_eq!(
        usage_label(UsageLabelKind::Plain, None, UsageDisplayUnit::Credits),
        "Créditos gastados"
    );
    assert_eq!(
        usage_label(
            UsageLabelKind::LastResponse,
            None,
            UsageDisplayUnit::Credits
        ),
        "Créditos gastados (última respuesta)"
    );
    assert_eq!(
        usage_label(UsageLabelKind::Total, None, UsageDisplayUnit::Credits),
        "Créditos gastados (total)"
    );
    assert_eq!(
        usage_label(
            UsageLabelKind::DetailsPanel,
            None,
            UsageDisplayUnit::Credits
        ),
        "Créditos usados"
    );
}

#[test]
fn usage_label_uses_credits_wording_when_flag_disabled_even_if_unit_is_dollars() {
    let _flag = FeatureFlag::PricingTransparency.override_enabled(false);

    assert_eq!(
        usage_label(UsageLabelKind::Plain, Some(36.0), UsageDisplayUnit::Dollars),
        "Créditos gastados"
    );
}

#[test]
fn usage_label_uses_credits_wording_when_dollars_requested_but_cost_unavailable() {
    let _flag = FeatureFlag::PricingTransparency.override_enabled(true);

    assert_eq!(
        usage_label(UsageLabelKind::Plain, None, UsageDisplayUnit::Dollars),
        "Créditos gastados"
    );
}
