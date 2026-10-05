import type {ReactNode} from 'react';
import clsx from 'clsx';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import CodeBlock from '@theme/CodeBlock';
import ThemedImage from '@theme/ThemedImage';
import {useBaseUrlUtils} from '@docusaurus/useBaseUrl';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
// Written by tools/gen_docs.py (gated by gen_docs.py --check): the install line, the code sample and its real
// output, and the palette swatches. Nothing here is typed by hand.
import home from '@site/src/data/home.json';
// Written by tools/home_figures.py with the PNGs under static/img/home/ (refreshed by the weekly live-tests-cron):
// each figure's name, alt text, caption and pixel size.
import figures from '@site/src/data/home_figures.json';
import styles from './index.module.css';

type FeatureItem = {
  title: string;
  to: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Any identifier',
    to: '/docs/concepts/identity',
    description: (
      <>
        Pass the team ids you already have — ESPN ids, nflverse or FanGraphs
        abbreviations, CFBD names, nba_api ids, NHL codes — and sdvplot resolves
        them, season-aware, without ever guessing.
      </>
    ),
  },
  {
    title: 'Logos for every era',
    to: '/docs/concepts/seasons-and-eras',
    description: (
      <>
        Logos and wordmarks come from the SportsDataverse logo archive with season
        ranges, so the 2010 Raiders get the Oakland mark.
      </>
    ),
  },
  {
    title: 'Team colors',
    to: '/docs/concepts/colors',
    description: (
      <>
        <code>palette()</code> returns a plain <code>{'{team: hex}'}</code> mapping
        that seaborn, Plotly, Altair and Bokeh accept as-is.
      </>
    ),
  },
  {
    title: 'Headshots',
    to: '/docs/tutorials/headshots',
    description: (
      <>
        ESPN athlete ids for the NFL, NBA, WNBA, MLB, NHL and college football and
        basketball, and NFL gsis ids through the nflverse player table, matching
        sdvplotR.
      </>
    ),
  },
  {
    title: 'pandas and polars',
    to: '/docs/concepts/identity#containers',
    description: (
      <>
        Scalars, lists, numpy arrays and pandas/polars Series in, the same
        container back — the pandas index kept.
      </>
    ),
  },
  {
    title: 'Part of the SportsDataverse',
    to: 'https://sportsdataverse.org',
    description: (
      <>
        The Python counterpart to{' '}
        <Link to="https://sdvplotR.sportsdataverse.org">sdvplotR</Link>, built on
        the same archive as{' '}
        <Link to="https://py.sportsdataverse.org">sdv-py</Link>.
      </>
    ),
  },
];

// A card per blurb; the title is the link, so the description can still hold links of its own.
function Feature({title, to, description}: FeatureItem): ReactNode {
  return (
    <div className={clsx('col col--4', styles.feature)}>
      <div className={clsx('card', styles.card)}>
        <h3 className={styles.cardTitle}>
          <Link to={to}>{title}</Link>
        </h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

function HomepageHeader(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <h1 className="hero__title">{siteConfig.title}</h1>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/intro">
            Getting Started
          </Link>
          <Link
            className="button button--outline button--secondary button--lg"
            to="/docs/reference/">
            API reference
          </Link>
        </div>
      </div>
    </header>
  );
}

// The install line, a sample that runs offline against the bundled index, and that sample's output
// in the theme's output style (.sdv-output).
function TryIt(): ReactNode {
  return (
    <section className={styles.section}>
      <div className="container">
        <h2>Install and try it</h2>
        <CodeBlock language="bash">{home.install}</CodeBlock>
        <CodeBlock language="python">{home.sample}</CodeBlock>
        <div className="sdv-output">
          <CodeBlock language="text">{home.output}</CodeBlock>
        </div>
        <p>
          These calls run offline against the team index bundled with the
          package. <Link to="/docs/intro">Getting started</Link> lists the extras.
        </p>
      </div>
    </section>
  );
}

// Figures drawn by sdvplot's own matplotlib adapter, a light and a dark PNG each; ThemedImage shows the one that
// matches the color mode.
function Figures(): ReactNode {
  const {withBaseUrl} = useBaseUrlUtils();
  return (
    <section className={styles.section}>
      <div className="container">
        <h2>What it draws</h2>
        <div className={styles.figures}>
          {figures.map((f) => (
            <figure key={f.name} className={styles.figure}>
              <ThemedImage
                alt={f.alt}
                width={f.width}
                height={f.height}
                loading="lazy"
                sources={{
                  light: withBaseUrl(`/img/home/${f.name}-light.png`),
                  dark: withBaseUrl(`/img/home/${f.name}-dark.png`),
                }}
              />
              <figcaption>{f.caption}</figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}

function Swatches(): ReactNode {
  return (
    <section className={styles.section}>
      <div className="container">
        <h2>Team colors from palette()</h2>
        <ul className={styles.swatches}>
          {home.swatches.map((s) => (
            <li key={`${s.league}-${s.team}`} className={styles.swatch}>
              <span className={styles.chips} aria-hidden="true">
                <span className={styles.chip} style={{background: s.primary}} />
                <span className={styles.chip} style={{background: s.secondary}} />
              </span>
              <span className={styles.swatchName}>{s.name}</span>
              <span className={styles.swatchMeta}>{s.league}</span>
              <code className={styles.swatchHex}>
                {s.primary} {s.secondary}
              </code>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={siteConfig.title}
      description={siteConfig.tagline}>
      <HomepageHeader />
      <main>
        <TryIt />
        <Figures />
        <Swatches />
        <section className={styles.features}>
          <div className="container">
            <div className="row">
              {FeatureList.map((props, idx) => (
                <Feature key={idx} {...props} />
              ))}
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
