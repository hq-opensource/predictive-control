import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  Svg: React.ComponentType<React.ComponentProps<'svg'>>;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Hybrid Control Strategy (MPC + RTC)',
    Svg: require('@site/static/img/control1.svg').default,
    description: (
      <>
        Combines Model Predictive Control for proactive energy planning with
        Real-Time Control for immediate, reactive adjustments, ensuring both
        optimal energy usage and strict adherence to power limits.
      </>
    ),
  },
  {
    title: 'Flexible Device Integration',
    Svg: require('@site/static/img/devices.svg').default,
    description: (
      <>
        Provides a standardized `DeviceMPC` interface for seamless integration
        of various controllable devices (e.g., HVAC, water heaters, electric
        vehicles, batteries), enabling modular and scalable energy management.
      </>
    ),
  },
  {
    title: 'User-Centric Optimization',
    Svg: require('@site/static/img/user.svg').default,
    description: (
      <>
        Balances energy cost minimization with user comfort by incorporating
        dynamic pricing, prioritizing less critical devices during curtailment,
        and utilizing thermal models for accurate predictions.
      </>
    ),
  },
];

function Feature({title, Svg, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
