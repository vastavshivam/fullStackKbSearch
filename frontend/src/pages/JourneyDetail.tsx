import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './JourneyDetail.css';

const dummyJourneys = [
  {
    id: 1,
    title: 'Welcome Series',
    description: 'Introduce your brand with automated welcome messages.',
    icon: '📩',
  },
  {
    id: 2,
    title: 'Abandoned Cart',
    description: 'Remind users of what they left behind.',
    icon: '🛒',
  },
  {
    id: 3,
    title: 'Re-engagement',
    description: 'Win back users with personalized incentives.',
    icon: '💬',
  },
  {
    id: 4,
    title: 'Product Launch',
    description: 'Announce your new products with flair.',
    icon: '🚀',
  },
];

export default function JourneyDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const journey = dummyJourneys.find(j => j.id === Number(id));

  if (!journey) {
    return (
      <div className="journey-detail">
        <h2>Journey Not Found</h2>
        <button onClick={() => navigate('/journeys')}>← Back to Journeys</button>
      </div>
    );
  }

  return (
    <div className="journey-detail">
      <h1>{journey.icon} {journey.title}</h1>
      <p>{journey.description}</p>

      <div className="journey-info-card">
        <h3>Journey ID: {journey.id}</h3>
        <p>This journey is meant to automate {journey.title.toLowerCase()} related tasks.</p>
      </div>

      <div className="journey-actions">
        <button onClick={() => navigate('/journeys')}>← Back</button>
        <button className="journey-cta" onClick={() => alert('Edit feature coming soon!')}>Edit Journey</button>
      </div>
    </div>
  );
}
