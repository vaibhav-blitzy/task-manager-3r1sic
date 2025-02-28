import React, { useState, useCallback, useEffect, useMemo } from 'react';
import classNames from 'classnames'; // version ^2.3.2
import { 
  DndContext, 
  DragOverlay, 
  useSensors, 
  useSensor, 
  PointerSensor, 
  closestCorners 
} from '@dnd-kit/core'; // version ^6.0.0
import { 
  arrayMove, 
  SortableContext, 
  useSortable, 
  verticalListSortingStrategy 
} from '@dnd-kit/sortable'; // version ^7.0.0
import { toast } from 'react-toastify'; // version ^9.1.0

import TaskCard, { TaskCardProps } from '../../molecules/TaskCard/TaskCard';
import { Task, TaskStatus, TaskStatusUpdate } from '../../../types/task';
import { Button } from '../../atoms/Button/Button';
import { useTaskStatusUpdate } from '../../../api/hooks/useTasks';
import useAuth from '../../../api/hooks/useAuth';
import { canPerformAction } from '../../../utils/permissions';

interface TaskBoardProps {
  tasks: Task[];
  projectId?: string;
  onTaskClick?: (task: Task) => void;
  onAddTask?: (status: TaskStatus) => void;
  className?: string;
}

interface Column {
  id: string;
  title: string;
  tasks: Task[];
  status: TaskStatus;
}

interface DragState {
  active: Task | null;
  over: Column | null;
}

/**
 * Converts TaskStatus enum values to human-readable labels
 */
const getTaskStatusLabel = (status: TaskStatus): string => {
  switch (status) {
    case TaskStatus.CREATED:
      return 'To Do';
    case TaskStatus.ASSIGNED:
      return 'Assigned';
    case TaskStatus.IN_PROGRESS:
      return 'In Progress';
    case TaskStatus.ON_HOLD:
      return 'On Hold';
    case TaskStatus.IN_REVIEW:
      return 'In Review';
    case TaskStatus.COMPLETED:
      return 'Completed';
    case TaskStatus.CANCELLED:
      return 'Cancelled';
    default:
      return status;
  }
};

/**
 * Creates the default column structure for the task board
 */
const getDefaultColumns = (tasks: Task[]): Column[] => {
  // Define the visible columns with our preferred order
  const visibleStatuses = [
    TaskStatus.CREATED,
    TaskStatus.IN_PROGRESS,
    TaskStatus.IN_REVIEW,
    TaskStatus.COMPLETED
  ];
  
  // Create columns with friendly titles
  const columns: Column[] = visibleStatuses.map(status => ({
    id: status,
    title: getTaskStatusLabel(status),
    tasks: [],
    status: status
  }));

  // Group tasks by status
  tasks.forEach(task => {
    const column = columns.find(col => col.status === task.status);
    if (column) {
      column.tasks.push(task);
    } else {
      // If task has a status that's not in our visible columns,
      // add to the appropriate column based on workflow stage
      if (task.status === TaskStatus.ASSIGNED) {
        // Put assigned tasks in the "To Do" column
        const todoColumn = columns.find(col => col.status === TaskStatus.CREATED);
        if (todoColumn) todoColumn.tasks.push(task);
      } else if (task.status === TaskStatus.ON_HOLD) {
        // Put on-hold tasks in the "In Progress" column
        const inProgressColumn = columns.find(col => col.status === TaskStatus.IN_PROGRESS);
        if (inProgressColumn) inProgressColumn.tasks.push(task);
      } else if (task.status === TaskStatus.CANCELLED) {
        // Put cancelled tasks in the "Completed" column
        const completedColumn = columns.find(col => col.status === TaskStatus.COMPLETED);
        if (completedColumn) completedColumn.tasks.push(task);
      } else if (columns.length > 0) {
        // Fallback: add to first column
        columns[0].tasks.push(task);
      }
    }
  });

  return columns;
};

/**
 * Wrapper component for TaskCard that makes it sortable within columns
 */
const SortableTaskCard = ({ task, onClick }: { task: Task; onClick?: (task: Task) => void }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({
    id: task.id,
    data: {
      type: 'task',
      task
    }
  });

  const style = {
    transform: transform ? `translate3d(${transform.x}px, ${transform.y}px, 0)` : undefined,
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 1 : 0
  };

  return (
    <div 
      ref={setNodeRef} 
      style={style} 
      {...attributes} 
      {...listeners}
      className="mb-2"
    >
      <TaskCard 
        task={task} 
        onClick={onClick ? () => onClick(task) : undefined}
        draggable
        className="cursor-grab active:cursor-grabbing"
      />
    </div>
  );
};

/**
 * Component that renders a single column of tasks with a title and add button
 */
const TaskColumn = ({ 
  column, 
  onAddTask, 
  onTaskClick,
  canEdit
}: { 
  column: Column; 
  onAddTask?: () => void; 
  onTaskClick?: (task: Task) => void;
  canEdit: boolean;
}) => {
  return (
    <div className="flex flex-col w-72 bg-gray-100 rounded-md p-3 min-h-[50vh] max-h-[80vh]">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold text-gray-700">
          {column.title} <span className="text-gray-500 text-sm ml-1">({column.tasks.length})</span>
        </h3>
      </div>

      <div className="overflow-y-auto flex-grow">
        <SortableContext items={column.tasks.map(t => t.id)} strategy={verticalListSortingStrategy}>
          {column.tasks.map(task => (
            <SortableTaskCard 
              key={task.id} 
              task={task} 
              onClick={onTaskClick}
            />
          ))}
        </SortableContext>
      </div>

      {onAddTask && canEdit && (
        <Button
          variant="outline"
          size="sm"
          onClick={onAddTask}
          className="w-full mt-2"
          icon={<span>+</span>}
        >
          Add Task
        </Button>
      )}
    </div>
  );
};

/**
 * Main component for displaying and managing tasks in a Kanban board layout
 */
const TaskBoard: React.FC<TaskBoardProps> = ({
  tasks,
  projectId,
  onTaskClick,
  onAddTask,
  className
}) => {
  const { user } = useAuth();
  const [columns, setColumns] = useState<Column[]>([]);
  const [dragState, setDragState] = useState<DragState>({
    active: null,
    over: null
  });

  const { updateStatus, isLoading } = useTaskStatusUpdate();

  // Configure drag sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5, // 5px of movement required to start dragging
      },
    })
  );

  // Update columns when tasks prop changes
  useEffect(() => {
    setColumns(getDefaultColumns(tasks));
  }, [tasks]);

  // Handle drag start
  const handleDragStart = useCallback((event: any) => {
    const { active } = event;
    if (!active) return;

    const taskId = active.id.toString();
    const task = tasks.find(t => t.id === taskId);
    if (task) {
      setDragState(prev => ({
        ...prev,
        active: task
      }));
    }
  }, [tasks]);

  // Handle drag over
  const handleDragOver = useCallback((event: any) => {
    const { active, over } = event;
    if (!active || !over) return;

    const overId = over.id.toString();
    const column = columns.find(col => col.id === overId);
    if (column) {
      setDragState(prev => ({
        ...prev,
        over: column
      }));
    }
  }, [columns]);

  // Handle drag end (task status change)
  const handleDragEnd = useCallback((event: any) => {
    const { active, over } = event;
    if (!active || !over) {
      setDragState({ active: null, over: null });
      return;
    }

    const activeId = active.id.toString();
    const overId = over.id.toString();

    // Find the task
    const task = tasks.find(t => t.id === activeId);
    
    // Find the target column
    const column = columns.find(col => col.id === overId);

    // If the task is valid and being moved to a different status
    if (task && column && task.status !== column.status) {
      // Update the task status
      const newStatus: TaskStatusUpdate = {
        status: column.status
      };

      updateStatus({
        taskId: task.id,
        status: newStatus
      }).catch((err) => {
        toast.error(`Failed to update task status: ${err.message || 'Unknown error'}`);
      });
    }

    // Reset drag state
    setDragState({ active: null, over: null });
  }, [tasks, columns, updateStatus]);

  // Check if user has permission to edit tasks
  const canEdit = useMemo(() => {
    return user ? canPerformAction(user, 'update', { type: 'task' }) : false;
  }, [user]);

  // Handle add task for specific column
  const handleAddTask = useCallback((status: TaskStatus) => {
    if (onAddTask) {
      onAddTask(status);
    }
  }, [onAddTask]);

  return (
    <div className={classNames("task-board", className)}>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 overflow-x-auto pb-4">
          {columns.map(column => (
            <TaskColumn
              key={column.id}
              column={column}
              onTaskClick={onTaskClick}
              onAddTask={onAddTask ? () => handleAddTask(column.status) : undefined}
              canEdit={canEdit}
            />
          ))}
        </div>

        <DragOverlay>
          {dragState.active ? (
            <TaskCard
              task={dragState.active}
              className="w-72 shadow-xl"
            />
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
};

export default TaskBoard;