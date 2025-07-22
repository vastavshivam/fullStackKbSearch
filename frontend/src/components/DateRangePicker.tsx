import React, { useState } from 'react';
import { format } from 'date-fns';

export default function DateRangePicker({ onRangeChange }: { onRangeChange: (start: string, end: string) => void }) {
  const [start, setStart] = useState(() => format(new Date(), 'yyyy-MM-dd'));
  const [end, setEnd] = useState(() => format(new Date(), 'yyyy-MM-dd'));

  const handleChange = () => onRangeChange(start, end);

  return (
    <div className="date-range-picker">
      <label>From:</label>
      <input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
      <label>To:</label>
      <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
      <button onClick={handleChange}>Apply</button>
    </div>
  );
}