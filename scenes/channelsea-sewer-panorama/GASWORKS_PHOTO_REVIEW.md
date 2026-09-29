# Gasworks and waterfront chimney photographs

Reviewed 27 September 2026 after the author's further references.

## Northern waterfront, 1902

`reference/Images and Figures/Figure2_3 Abbey Mills Ingham Clarke & Co Bromley Gas Works 1902.jpg`
shows six readily distinguishable shafts: a dominant round shaft whose crown
is cropped at the top, shorter square masonry stacks with projecting caps,
a slender dark flue and more distant tall shafts. The waterfront buildings
have arched windows, curved gable/parapet profiles and retaining-wall openings.
These inform forms and relative silhouettes, not absolute heights or every
stack's ground position.

Preserve the author's earlier orientation correction: this is the northward
Channelsea view with West Ham gas holders behind chemical works. The original
filename's Bromley attribution is not adopted. Foreground chimneys must not
all be assigned to West Ham Gas Works.

The newly archived original Goad **F19, July 1893**, identifies Langthorne
Chemical Works and Robert Ingham, Clarke & Co.'s varnish works on the waterfront
opposite West Ham Gas Works. It is stored as
`reference/factory-building-survey/goad-f19.tiff`, from
[British Library scan BL 152673](https://commons.wikimedia.org/wiki/File:Insurance_Plan_of_London_North_East_District_Vol._F;_sheet_19_(BL_152673).tiff).
Matching individual shafts needs a registered camera comparison. These
east-bank works are currently legacy context beyond the detailed factory-pass
boundary; their existing guessed stacks remain guesses.

## Bromley production area, June 1924

The supplied `EPW010699.jpg` is archived at
`reference/factory-building-survey/bromley-1924-EPW010699.jpg`.
[Britain from Above](https://britainfromabove.org.uk/image/epw010699) dates it
to June 1924 and identifies Bromley-by-Bow Gas Works. It complements the already
archived EPW010697, which views the production ground from another angle.

The aerial distinguishes a taller rear utility/boiler stack from repeated
shorter retort-house roof stacks. The production skyline needs both scales.
The old production blocks can be compared with the 1893 OS plan. The small
square feature in the eastern utility range is **provisionally** interpreted as
the base of the taller rear stack. One round masonry stack has been added there;
its 32 m height, diameter, crown and photograph-to-plan correspondence remain
interpretations. Its record retains the OS pixel location and both aerial
references. Continuity from the mapped utility building into c1900 is an
inference, not a date established by the 1924 photograph.

Following the author's clarification that the goal is a close visual
reconstruction, the two production blocks now have paired broad roofs, similar
11 m eaves, and **24 shorter brick flues**: two rows of six on each block.
These approximate the rhythm of the aerial rather than claim an exact count.
Overall flue heights of 18.5–19.3 m leave short shafts above the roofs.
The previously low southern block is raised to match the scale of its northern
counterpart. Mapped ground footprints are retained.

Count, spacing and continuity from the aerial into c1900 are modelling choices.
OS stair projections have not been used as chimney symbols. This is enough
evidence for a plausible first reconstruction; future comparisons can refine it
without holding up the visual work. West Ham's own production stacks remain a
separate task from the chemical-works foreground of the 1902 photograph.

Reference images remain outside the public site and are not used as textures.
The base comparison is
`reference/factory-building-survey/review/bromley-boiler-stack-os.png`.
Local view: [Bromley Gas Works](http://localhost:4175/?view=factory-924).

```sh
python3 scripts/check_factory_buildings.py
python3 scripts/check_factory_yards.py
python3 scripts/review_factory_buildings.py --url http://localhost:4175 --gasworks-only
```
