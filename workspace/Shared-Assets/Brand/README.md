# Shared video identity

Status: brand setup is available; no visual identity has been selected or approved yet.

## What stays consistent

The shared identity can define typography, exact colour values, spacing and safe regions, caption hierarchy, logo use, title/lower-third/card treatments, and motion character (entrances, exits, easing and reading holds). Scene layout adapts to the footage and explanation; consistent branding does not require every scene to use the same composition.

After reviewing a representative polished treatment with the user, save approved tokens and constraints in `Shared-Assets/Brand/frame.md`, with YAML frontmatter and a dated/versioned revision. Use the installed HyperFrames creative skill's `references/design-spec.md` format. Don't invent approved colours or fonts to fill an empty template. Keep font files and licence/source notes with the actual selected assets.

For each new video, carry the approved revision into the composition's own `frame.md` and record its origin. This deliberate snapshot keeps earlier videos reproducible. Update active projects deliberately when branding changes; don't symlink every historic video to a mutable current theme. Reuse tested component sources from [the component index](../../Workflow/COMPONENTS.md), adapting content and phrase anchors.

Brand marks stay consistent across videos once chosen; each video's composition, look and sound still vary (`Workflow/STYLE.md`). This is an authoring convention, not a renderer feature that automatically styles arbitrary HTML.

## Reference material

Put reference screenshots and clips the user likes in `References/`, with a line each on what is liked about it (layout, colour, typography, motion). References are candidates for discussion, not licensed production assets or approved palettes.
