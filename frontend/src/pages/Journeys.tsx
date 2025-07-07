import React, { useState } from 'react';
import './Journeys.css';
import {
  LayoutGrid, List, PlusCircle, Search,
  TrendingUp, X, Trash2
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const initialJourneys = [
  {
    id: 1,
    title: "Welcome Series",
    description: "Introduce your brand with automated welcome messages.",
    icon: "📩",
  },
  {
    id: 2,
    title: "Abandoned Cart",
    description: "Remind users of what they left behind.",
    icon: "🛒",
  },
  {
    id: 3,
    title: "Re-engagement",
    description: "Win back users with personalized incentives.",
    icon: "💬",
  },
  {
    id: 4,
    title: "Product Launch",
    description: "Announce your new products with flair.",
    icon: "🚀",
  },
];

export default function JourneysPage() {
  const [view, setView] = useState<'grid' | 'list'>('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [journeys, setJourneys] = useState(initialJourneys);
  const [editModal, setEditModal] = useState<{ open: boolean; id: number | null }>({ open: false, id: null });

  const navigate = useNavigate();

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    const filtered = initialJourneys.filter(j =>
      j.title.toLowerCase().includes(value.toLowerCase())
    );
    setJourneys(filtered);
  };

  const handleCreateJourney = () => {
    const newJourney = {
      id: Date.now(),
      title: `Untitled Journey ${journeys.length + 1}`,
      description: "Describe your journey...",
      icon: "📝",
    };
    setJourneys([newJourney, ...journeys]);
  };

  const openEditModal = (id: number) => {
    setEditModal({ open: true, id });
  };

  const closeEditModal = () => {
    setEditModal({ open: false, id: null });
  };

  const handleEditChange = (key: 'title' | 'description', value: string) => {
    setJourneys(prev =>
      prev.map(j =>
        j.id === editModal.id ? { ...j, [key]: value } : j
      )
    );
  };

  const handleDelete = (id: number) => {
    const confirm = window.confirm("Are you sure you want to delete this journey?");
    if (confirm) {
      setJourneys(prev => prev.filter(j => j.id !== id));
    }
  };

  const selectedJourney = journeys.find(j => j.id === editModal.id);

  return (
    <div className="journey-wrapper">
      <header className="journey-header">
        <div className="journey-headline">
          <h1>📈 Journeys</h1>
          <p>Automate and optimize your marketing efforts with dynamic workflows.</p>
        </div>
        <div className="journey-toolbar">
          <div className="search-input">
            <Search size={18} />
            <input
              type="text"
              placeholder="Search journeys..."
              value={searchTerm}
              onChange={handleSearch}
            />
          </div>
          <button className="new-journey-btn" onClick={handleCreateJourney}>
            <PlusCircle size={18} /> New Journey
          </button>
          <div className="view-toggle">
            <button onClick={() => setView('grid')} className={view === 'grid' ? 'active' : ''}>
              <LayoutGrid size={18} />
            </button>
            <button onClick={() => setView('list')} className={view === 'list' ? 'active' : ''}>
              <List size={18} />
            </button>
          </div>
        </div>
      </header>

      <section className="journey-summary">
        <div className="summary-card">
          <TrendingUp size={20} />
          <div>
            <h4>Avg Open Rate</h4>
            <p>48%</p>
          </div>
        </div>
        <div className="summary-card">
          <TrendingUp size={20} />
          <div>
            <h4>Click Rate</h4>
            <p>22%</p>
          </div>
        </div>
        <div className="summary-card">
          <TrendingUp size={20} />
          <div>
            <h4>Total Journeys</h4>
            <p>{journeys.length}</p>
          </div>
        </div>
      </section>

      <main className={`journey-list ${view}`}>
        {journeys.length === 0 ? (
          <div className="no-results">No journeys found.</div>
        ) : (
          journeys.map((journey) => (
            <div
              className="journey-card"
              key={journey.id}
              onClick={() => navigate(`/journeys/${journey.id}`)}
            >
              <div className="journey-icon">{journey.icon}</div>
              <div className="journey-content">
                <h2>{journey.title}</h2>
                <p>{journey.description}</p>
                <button
                  className="journey-cta"
                  onClick={(e) => {
                    e.stopPropagation();
                    openEditModal(journey.id);
                  }}
                >
                  Edit
                </button>
                <button
                  className="journey-delete"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(journey.id);
                  }}
                >
                  <Trash2 size={16} style={{ marginRight: 4 }} />
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </main>

      {editModal.open && selectedJourney && (
        <div className="modal-overlay">
          <div className="edit-modal">
            <button className="modal-close" onClick={closeEditModal}><X size={20} /></button>
            <h2>Edit Journey</h2>
            <input
              value={selectedJourney.title}
              onChange={(e) => handleEditChange('title', e.target.value)}
              placeholder="Journey Title"
            />
            <textarea
              value={selectedJourney.description}
              onChange={(e) => handleEditChange('description', e.target.value)}
              placeholder="Journey Description"
            ></textarea>
            <button className="journey-cta" onClick={closeEditModal}>Save</button>
          </div>
        </div>
      )}
    </div>
  );
}
