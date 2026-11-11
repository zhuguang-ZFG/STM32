# Third-party notices: web motion layers

The files in `vendor/` are unmodified release builds of the libraries below. Each library's full licence text is next to it as `vendor/<name>.LICENSE`. All of them are permissive (MIT, ISC or Apache-2.0), and they are only loaded into the headless Chromium page that renders a motion layer. matter-js, Zdog and MathJax are loaded only for the recipe that uses them (`physics`, `spin3d`, `formula`).

| File | Library | Version | Licence | Source |
|---|---|---|---|---|
| `vendor/anime.js` | anime.js | 4.5.0 | MIT | https://github.com/juliangarnier/anime |
| `vendor/rough.js` | Rough.js | 4.6.6 | MIT | https://github.com/rough-stuff/rough |
| `vendor/rough-notation.js` | Rough Notation | 0.5.1 | MIT | https://github.com/rough-stuff/rough-notation |
| `vendor/confetti.js` | canvas-confetti | 1.9.4 | ISC | https://github.com/catdad/canvas-confetti |
| `vendor/d3-geo.js` | d3-geo | 3.1.1 | ISC | https://github.com/d3/d3-geo |
| `vendor/d3-array.js` | d3-array | 3.2.4 | ISC | https://github.com/d3/d3-array |
| `vendor/topojson.js` | topojson-client | 3.1.0 | ISC | https://github.com/topojson/topojson-client |
| `vendor/land-110m.js` | world-atlas `land-110m.json` | 2.0.2 | ISC (`world-atlas.LICENSE`) | https://github.com/topojson/world-atlas |
| `vendor/matter.js` | matter-js (`build/matter.min.js`) | 0.20.0 | MIT | https://github.com/liabru/matter-js |
| `vendor/zdog.js` | Zdog (`dist/zdog.dist.min.js`) | 1.1.3 | MIT (`zdog.LICENSE`; upstream states "Licensed MIT" and ships no licence file, so the standard text with its copyright line is reproduced) | https://github.com/metafizzy/zdog |
| `vendor/mathjax-tex-svg.js` | MathJax (`es5/tex-svg-full.js`) | 3.2.2 | Apache-2.0 (`mathjax.LICENSE`; the package has no NOTICE file) | https://github.com/mathjax/MathJax |

**Map data.** world-atlas `land-110m` comes from [Natural Earth](https://www.naturalearthdata.com/), which is in the public domain. Our only change is a wrapper: the JSON is assigned to `window.WORLD_LAND` so that the page can load it without a file fetch. It contains land outlines only, with no country borders. `map_route` therefore draws coastlines and routes, never political boundaries. If a map must show borders (for example, maps published in mainland China need an approval number), the producer must supply compliant artwork.

## Methods we learned from (no code copied)

- **[huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion)** (MIT, also bundled under `dependencies/`). From its 镜头语言 guide we took:
  - camera move durations (slow push 0.6–1.5 s, pull-out 0.8–2 s, whip about 0.28 s, slam 0.17 s);
  - the density rules behind `direction.camera_warnings`;
  - the list of paper and ink transitions we rebuilt in numpy (page turn, ink bloom, shards, tiles, cube).
- **[anidoodle](https://github.com/alexgreensh/anidoodle)** (Apache-2.0). From its motion grammar and camera notes we took ideas only:
  - interpolating zoom in log space;
  - a decaying arrival shake;
  - keeping quick moves as accents;
  - its list of effects to refuse (glitch, light sweeps, unmotivated particle bursts, plain cross-fades).

  We wrote our implementations from scratch in Python and JavaScript.
- **[perfect-freehand](https://github.com/steveruiz/perfect-freehand)** (MIT). The idea behind the pressure-sensitive lines and arrows: a stroke's width follows simulated pen pressure, with tapered ends and thinning where the pen moves fastest. Our `stroke_assets.pressure_widths` is a separate, much smaller Python model (a minimum-jerk speed profile, a landing swell and a lift-off taper); no code was copied.
- **[awesome-ai-motion](https://github.com/guanmo-ai/awesome-ai-motion)**: a survey of 1,417 AI-made motion works. We used it only to rank which effect families to build. No work, prompt or asset from it is included.
