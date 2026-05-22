import { create } from "zustand";

import * as api from "../api/client";
import type { Book, Chapter, Topic, Connection } from "../types";

interface BookStore {
  // State
  books: Book[];
  selectedBook: Book | null;
  chapters: Chapter[];
  allTopics: Topic[];
  connections: Connection[];
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchBooks: () => Promise<void>;
  uploadBook: (file: File) => Promise<void>;
  deleteBook: (bookId: number) => Promise<void>;
  selectBook: (book: Book) => Promise<void>;
  fetchAllTopics: (bookId: number) => Promise<void>;
  fetchBookConnections: (bookId: number) => Promise<void>;
}

export const useBookStore = create<BookStore>((set, get) => ({
  books: [],
  selectedBook: null,
  chapters: [],
  allTopics: [],
  connections: [],
  isLoading: false,
  error: null,

  fetchBooks: async () => {
    set({ isLoading: true, error: null });
    try {
      const books = await api.getBooks();
      set({ books });
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ isLoading: false });
    }
  },

  uploadBook: async (file) => {
    set({ isLoading: true, error: null });
    try {
      const book = await api.uploadBook(file);
      set((state) => ({ books: [book, ...state.books] }));
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ isLoading: false });
    }
  },

  deleteBook: async (bookId) => {
    set({ isLoading: true, error: null });
    try {
      await api.deleteBook(bookId);
      const { selectedBook } = get();
      set((state) => ({
        books: state.books.filter((b) => b.id !== bookId),
        selectedBook: selectedBook?.id === bookId ? null : selectedBook,
        chapters: selectedBook?.id === bookId ? [] : state.chapters,
        allTopics: selectedBook?.id === bookId ? [] : state.allTopics,
        connections: selectedBook?.id === bookId ? [] : state.connections,
      }));
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ isLoading: false });
    }
  },

  selectBook: async (book) => {
    set({ selectedBook: book, chapters: [], allTopics: [], connections: [], error: null, isLoading: true });
    try {
      const chapters = await api.getChapters(book.id);
      set({ chapters });
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchAllTopics: async (bookId) => {
    try {
      const allTopics = await api.getAllTopicsForBook(bookId);
      set({ allTopics });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  fetchBookConnections: async (bookId) => {
    try {
      const connections = await api.getBookConnections(bookId);
      set({ connections });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },
}));
