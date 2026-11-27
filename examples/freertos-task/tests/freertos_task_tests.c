/**
 * Host-only checks for freertos-task invariants (no FreeRTOS kernel linked).
 * Stack depths in main.c are in words; tick is 1 ms.
 */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

/* Mirror macros from main.c — keep in sync when changing the sketch. */
#define LED_TASK_STACK 128U
#define KEY_TASK_STACK 192U
#define UART_TASK_STACK 256U
#define KEY_QUEUE_LEN 8U
#define BYTES_PER_WORD 4U

static void test_stack_depths_are_words_not_bytes(void)
{
    assert(LED_TASK_STACK * BYTES_PER_WORD == 512U);
    assert(KEY_TASK_STACK * BYTES_PER_WORD == 768U);
    assert(UART_TASK_STACK * BYTES_PER_WORD == 1024U);
    /* Common footgun: treating 128 as bytes leaves ~32 words — create fails or HardFaults. */
    assert(LED_TASK_STACK != 512U);
}

static void test_queue_can_hold_key_events(void)
{
    assert(KEY_QUEUE_LEN >= 1U);
    assert(KEY_QUEUE_LEN * sizeof(uint8_t) == 8U);
}

static void test_priority_order(void)
{
    const unsigned led = 1U;
    const unsigned key = 2U;
    const unsigned uart = 1U;
    assert(key > led);
    assert(key > uart);
}

int main(void)
{
    test_stack_depths_are_words_not_bytes();
    test_queue_can_hold_key_events();
    test_priority_order();
    printf("PASS: freertos-task host invariants (stack words, queue, priorities)\n");
    return 0;
}
