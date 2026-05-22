import { create } from "zustand";

import * as api from "../api/client";
import type { TheoryContent, PracticalContent, QAMessage, TopicConnection } from "../types";

interface StudyStore {
  // Per-topic content — keyed by topicId so revisiting a topic is instant
  theory: Record<number, TheoryContent>;
  practical: Record<number, PracticalContent>;
  topicConnections: Record<number, TopicConnection[]>;

  // Q&A thread — resets when the user navigates to a new topic
  qaMessages: QAMessage[];

  // Loading / error state per content type
  theoryLoading: boolean;
  practicalLoading: boolean;
  connectionsLoading: boolean;
  qaLoading: boolean;
  error: string | null;

  // Actions
  fetchTheory: (topicId: number) => Promise<void>;
  fetchPractical: (topicId: number) => Promise<void>;
  fetchTopicConnections: (topicId: number) => Promise<void>;
  askQuestion: (bookId: number, question: string, topicId: number | null) => Promise<void>;
  clearQA: () => void;
}

export const useStudyStore = create<StudyStore>((set, get) => ({
  theory: {},
  practical: {},
  topicConnections: {},
  qaMessages: [],
  theoryLoading: false,
  practicalLoading: false,
  connectionsLoading: false,
  qaLoading: false,
  error: null,

  fetchTheory: async (topicId) => {
    // Return cached result immediately — no re-fetch needed
    if (get().theory[topicId]) return;
    set({ theoryLoading: true, error: null });
    try {
      const content = await api.getTheory(topicId);
      set((state) => ({ theory: { ...state.theory, [topicId]: content } }));
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ theoryLoading: false });
    }
  },

  fetchPractical: async (topicId) => {
    if (get().practical[topicId]) return;
    set({ practicalLoading: true, error: null });
    try {
      const content = await api.getPractical(topicId);
      set((state) => ({ practical: { ...state.practical, [topicId]: content } }));
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ practicalLoading: false });
    }
  },

  fetchTopicConnections: async (topicId) => {
    if (get().topicConnections[topicId]) return;
    set({ connectionsLoading: true, error: null });
    try {
      const connections = await api.getTopicConnections(topicId);
      set((state) => ({ topicConnections: { ...state.topicConnections, [topicId]: connections } }));
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ connectionsLoading: false });
    }
  },

  askQuestion: async (bookId, question, topicId) => {
    set({ qaLoading: true, error: null });
    try {
      const response = await api.askQuestion(bookId, question, topicId);
      set((state) => ({
        qaMessages: [...state.qaMessages, { question, response }],
      }));
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ qaLoading: false });
    }
  },

  clearQA: () => set({ qaMessages: [] }),
}));
