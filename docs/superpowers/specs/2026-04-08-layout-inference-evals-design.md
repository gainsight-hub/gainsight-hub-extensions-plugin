# Layout Inference Evals Design

## Goal

Add two evals to `build-extension` that test whether the agent infers the right structural layout from vague size/format hints in the prompt. These are distinct from existing design-quality evals (which test visual polish) — layout inference evals test whether the agent picks the correct structural form factor.

## Approach

Single-turn evals with transcript assertions. Consistent with existing evals like `polished-card` and `data-table`. No multi-turn — the agent should infer layout from the prompt alone.

## Eval Definitions

### Eval 17: `layout-hint-small`

**Prompt**: "Build a widget that shows our current app version, keep it really small and unobtrusive"

**Expected output**: Compact, minimal widget — badge, pill, status bar, or inline tag. Not a full card or section.

**Assertions**:

| Name | Text | Type |
|------|------|------|
| `compact-layout` | Widget uses a compact form factor — badge, pill, tag, bar, or inline element with tight dimensions (small max-width or max-height, minimal padding) rather than a full card or section layout | transcript |
| `minimal-footprint` | CSS constrains the widget size — uses small fixed dimensions, `display: inline-block`/`inline-flex`, `fit-content`, or tight max-width (under ~200px) to keep it unobtrusive | transcript |
| `restrained-styling` | Visual styling is understated — no large shadows, heavy borders, or prominent backgrounds; uses subtle treatments appropriate for a small utility element | transcript |
| `creates-valid-structure` | Creates widget.json with required fields and dist/content.html as an HTML fragment | transcript |

### Eval 18: `layout-hint-dashboard`

**Prompt**: "I need to see all our key metrics at a glance"

**Expected output**: Dashboard-style widget with multi-column grid or flexbox layout showing multiple metric cards/cells. Not a single stacked vertical list.

**Assertions**:

| Name | Text | Type |
|------|------|------|
| `grid-or-multicolumn` | Layout uses CSS grid, multi-column flexbox (flex-wrap), or explicit column structure to display metrics side-by-side rather than a single vertical stack | transcript |
| `multiple-metrics` | Widget shows 3+ distinct metrics (e.g., different KPIs, health scores, counts) — not just one number | transcript |
| `metric-visual-treatment` | Each metric has intentional visual treatment — large prominent number with smaller label, color coding, icon, or trend indicator | transcript |
| `scannable-hierarchy` | Layout is designed for quick scanning — metric values are visually dominant (larger font-size or bolder weight) over labels and secondary info | transcript |
| `creates-valid-structure` | Creates widget.json with required fields and dist/content.html as an HTML fragment | transcript |

## Implementation

1. Add both eval objects to `skills/build-extension/evals/evals.json` with IDs 17 and 18
2. Run with_skill + without_skill using existing eval runner
3. Grade and update benchmark
