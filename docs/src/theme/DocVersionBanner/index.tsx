import React, {type ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import {useDocsVersion, useVersions} from '@docusaurus/plugin-content-docs/client';
import {ThemeClassNames} from '@docusaurus/theme-common';
import DocVersionBanner from '@theme-original/DocVersionBanner';
import type {Props} from '@theme/DocVersionBanner';

// Wraps the version banner (`docusaurus swizzle @docusaurus/theme-classic DocVersionBanner --wrap`). The root docs
// (`current`, labelled main) are also the latest version, so Docusaurus's own "unreleased" banner would point readers
// at the page they are on: on main ahead of its release, this one names the release `pip install sdvplot` gives and
// links its snapshot instead. docusaurus.config.ts sets that banner only while pyproject's version is unreleased.
export default function DocVersionBannerWrapper(props: Props): ReactNode {
  const version = useDocsVersion();
  const released = useVersions(undefined).find((v) => v.name !== 'current');
  const {projectVersion} = useDocusaurusContext().siteConfig.customFields as {projectVersion: string};
  if (version.version !== 'current' || version.banner !== 'unreleased') {
    return <DocVersionBanner {...props} />;
  }
  const releasedIntro = released?.docs.find((doc) => doc.id === released.mainDocId);
  return (
    <div
      className={clsx(props.className, ThemeClassNames.docs.docVersionBanner, 'alert alert--warning margin-bottom--md')}
      role="alert">
      These pages document sdvplot <b>{projectVersion}</b> from main, which is not released yet.
      {released && releasedIntro && (
        <>
          {' '}
          <code>pip install sdvplot</code> installs {released.label}: see the{' '}
          <Link to={releasedIntro.path}>{released.label} documentation</Link>.
        </>
      )}
    </div>
  );
}
