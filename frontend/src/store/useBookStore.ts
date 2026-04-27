import { create } from "zustand";

import * as api from "../api/client";
import type { Book, Chapter } from "../types";

interface BookStore {
  // State
  books: Book[];
  selectedBook: Book | null;
  chapters: Chapter[];
  selectedChapter: Chapter | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchBooks: () => Promise<void>;
  uploadBook: (file: File) => Promise<void>;
  deleteBook: (bookId: number) => Promise<void>;
  selectBook: (book: Book) => Promise<void>;
  selectChapter: (chapter: Chapter) => void;
}

export const useBookStore = create<BookStore>((set, get) => ({
  books: [],
  selectedBook: null,
  chapters: [],
  selectedChapter: null,
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
        // clear selection if the deleted book was selected
        selectedBook: selectedBook?.id === bookId ? null : selectedBook,
        chapters: selectedBook?.id === bookId ? [] : state.chapters,
        selectedChapter: selectedBook?.id === bookId ? null : state.selectedChapter,
      }));
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ isLoading: false });
    }
  },

  selectBook: async (book) => {
    set({ selectedBook: book, chapters: [], selectedChapter: null, error: null, isLoading: true });
    try {
      const chapters = await api.getChapters(book.id);
      set({ chapters });
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ isLoading: false });
    }
  },

  selectChapter: (chapter) => {
    set({ selectedChapter: chapter });
  },
}));
