import type {ReactNode} from 'react';
import clsx from 'clsx';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import useBaseUrl from '@docusaurus/useBaseUrl';
import styles from './index.module.css';

type FeatureItem = {
  title: string;
  imageUrl?: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Any identifier',
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
    description: (
      <>
        Logos and wordmarks come from the SportsDataverse logo archive with season
        ranges, so the 2010 Raiders get the Oakland mark.
      </>
    ),
  },
  {
    title: 'Team colors',
    description: (
      <>
        <code>palette()</code> returns a plain <code>{'{team: hex}'}</code> mapping
        that seaborn, Plotly, Altair and Bokeh accept as-is.
      </>
    ),
  },
  {
    title: 'Headshots',
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
    description: (
      <>
        Scalars, lists, numpy arrays and pandas/polars Series in, the same
        container back — the pandas index kept.
      </>
    ),
  },
  {
    title: 'Part of the SportsDataverse',
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

function Feature({imageUrl, title, description}: FeatureItem): ReactNode {
  const imgUrl = useBaseUrl(imageUrl);
  return (
    <div className={clsx('col col--4', styles.feature)}>
      {imgUrl && (
        <div className="text--center">
          <img className={styles.featureImage} src={imgUrl} alt={title} />
        </div>
      )}
      <h3>{title}</h3>
      <p>{description}</p>
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

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={siteConfig.title}
      description={siteConfig.tagline}>
      <HomepageHeader />
      <main>
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
