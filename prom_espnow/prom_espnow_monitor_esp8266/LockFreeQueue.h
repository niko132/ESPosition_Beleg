#ifndef LOCKFREEQUEUE_H
#define LOCKFREEQUEUE_H

#include <Arduino.h>

#define QUEUE_SIZE 100 // about 5 are enough

template <typename T>
class LockFreeQueue {
private:
    T queue[QUEUE_SIZE];
    volatile uint8_t head;
    volatile uint8_t tail;

public:
    LockFreeQueue();
    bool enqueue(const T& value);
    bool dequeue(T& value);
    bool isEmpty();
    bool isFull();
};


template <typename T>
LockFreeQueue<T>::LockFreeQueue() : head(0), tail(0) {}

template <typename T>
bool LockFreeQueue<T>::enqueue(const T& value) {
    uint8_t next = (head + 1) % QUEUE_SIZE;
    if (next == tail) {
        return false; // Queue is full
    }
    queue[head] = value;  // Create a copy of the object in the queue
    head = next;
    return true;
}

template <typename T>
bool LockFreeQueue<T>::dequeue(T& value) {
    if (head == tail) {
        return false; // Queue is empty
    }
    value = queue[tail];  // Create a copy of the object being dequeued
    tail = (tail + 1) % QUEUE_SIZE;
    return true;
}

template <typename T>
bool LockFreeQueue<T>::isEmpty() {
    return head == tail;
}

template <typename T>
bool LockFreeQueue<T>::isFull() {
    return (head + 1) % QUEUE_SIZE == tail;
}

#endif // LOCKFREEQUEUE_H
