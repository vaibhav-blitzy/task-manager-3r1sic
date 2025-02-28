import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux'; // ^8.1.0
import { RootState, AppDispatch } from './index';

/**
 * Typed version of the useDispatch hook for use throughout the application.
 * Provides proper TypeScript typing for the dispatch function based on our store configuration.
 * 
 * @returns A properly typed dispatch function for dispatching actions to the Redux store
 */
export const useAppDispatch = () => useDispatch<AppDispatch>();

/**
 * Typed version of the useSelector hook for use throughout the application.
 * Provides proper TypeScript typing for state selection based on our RootState type.
 * 
 * Use this hook whenever selecting data from the Redux store to ensure proper type checking.
 */
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;