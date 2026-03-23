# Campaign Output Structure Template

This template defines the expected folder structure and file names
for every completed campaign in `outputs/<brand>/<YYYY-MM-DD>/`.

---

## Required Folder Structure

```
outputs/<brand>/<YYYY-MM-DD-HHMMSS>/
├── campaign_summary.md          ← Links all deliverables
├── validation_report.md         ← Validator quality scores
│
├── intelligence/
│   ├── competitor_analysis.md   ← SWOT, keyword gaps, positioning map
│   ├── content_preferences.md   ← Top content hooks + formats per platform
│   └── meta_ads_analysis.md     ← Competitor ad hooks, personas, CTAs
│
├── copy/
│   └── copy.md                  ← Headlines, body copy, CTAs
│
├── seo/
│   └── seo.md                   ← Keywords, meta descriptions, content briefs
│
├── social/
│   └── social_media.md          ← 30 posts across IG/YT/TikTok/FB/LI
│
├── ads/
│   └── ad_campaigns.md          ← 10 Google + 10 Meta ad variants
│
└── brand_strategy/
    └── brand_strategy.md        ← Positioning, messaging framework
```

---

## campaign_summary.md Format

```markdown
# Campaign Summary — {brand}

**Run ID:** {run_id}
**Generated:** {datetime}

## Intelligence Files

- [Competitor Analysis](intelligence/competitor_analysis.md)
- [Content Preferences](intelligence/content_preferences.md)
- [Meta Ads Analysis](intelligence/meta_ads_analysis.md)

## Deliverables

- **Copywriting**: copy/copy.md
- **SEO**: seo/seo.md
- **Social Media**: social/social_media.md
- **Ad Campaigns**: ads/ad_campaigns.md
- **Brand Strategy**: brand_strategy/brand_strategy.md

## Validation

- **Report**: validation_report.md
- **Passed:** {N}/{total}
- **Average Score:** {score}/10
```

---

## Quality Checklist

Before marking a campaign complete, verify:

- [ ] All intelligence files written to `intelligence/`
- [ ] All creative deliverables written to correct subdirs
- [ ] `campaign_summary.md` links all files correctly
- [ ] `validation_report.md` shows pass/fail for all outputs
- [ ] No placeholder text remains in deliverables
- [ ] Brand voice matches `clients/<brand>/brand_guidelines.md`
- [ ] No competitor clichés (check against `competitor_intel/<brand>/`)
- [ ] All 30 social posts generated (6 per platform)
- [ ] All 20 ad variants generated (10 Google + 10 Meta)
