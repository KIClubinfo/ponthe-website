import { useState } from 'react';
import Cookies from 'js-cookie';

// Multi-selection of pictures, shared by the public gallery and the
// management page: the mode, the selected names, and the zip download.
export default function useSelection(slug) {
  const [selectionMode, setSelectionMode] = useState(false);
  const [selected, setSelected] = useState(new Set());

  //Enter/leave the multi-selection mode; leaving clears the selection
  const toggleSelectionMode = () => {
    setSelectionMode(prev => !prev);
    setSelected(new Set());
  };

  //Add/remove one picture from the selection
  const toggleSelect = (fileFullName) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(fileFullName)) {
        next.delete(fileFullName);
      } else {
        next.add(fileFullName);
      }
      return next;
    });
  };

  //Download the selection as a single zip built by the backend
  const downloadSelected = async () => {
    if (selected.size === 0) return;
    const downloadOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': Cookies.get('csrftoken') },
      body: JSON.stringify({ slug: slug, file_full_names: Array.from(selected) })
    };
    try {
      const response = await fetch('/api/gallery/pics/download/', downloadOptions);
      if (!response.ok) {
        // The backend says why: too many pictures, too heavy, gone...
        let message = 'Impossible de télécharger les photos sélectionnées.';
        try {
          const data = await response.json();
          if (data && data.message) message = data.message;
        } catch (parseError) {
          // Not JSON (error page of a proxy, ...): keep the generic message
        }
        alert(message);
        return;
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = slug + '-selection.zip';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.log(err);
      alert('Erreur réseau : impossible de contacter le serveur.');
    }
  };

  return { selectionMode, selected, toggleSelectionMode, toggleSelect, downloadSelected };
}
