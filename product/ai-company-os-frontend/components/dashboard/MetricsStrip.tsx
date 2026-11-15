"use client";
import fixture from '../../fixtures/office.snapshot.json';
import MetricCards from '../../design-system/MetricCards';
export default function MetricsStrip(){return <MetricCards metrics={fixture.metrics}/>;}
