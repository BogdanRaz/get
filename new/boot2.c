#include <stdint.h>
#include "mmio.h"

extern uint32_t _stack0_top;
extern void Reset_Handler(void);

#define QSPI_BASE   0x40020000
#define QSPI_SCLK   (QSPI_BASE + 0x04)
#define QSPI_SD0    (QSPI_BASE + 0x08)
#define QSPI_SD1    (QSPI_BASE + 0x0C)
#define QSPI_SD2    (QSPI_BASE + 0x10)
#define QSPI_SD3    (QSPI_BASE + 0x14)
#define SCLK_MASK   (3 << 4 | 1 << 0)
#define FAST_8MA    (2 << 4 | 1 << 0)
#define SD_MASK     (3 << 4 | 3 << 0)
#define SSI_BASE    0x18000000
#define SSI_CTRL0   (SSI_BASE + 0x00)

#define SSI_ENR     (SSI_BASE + 0x08)
#define SSI_BAUDR   (SSI_BASE + 0x14)
#define SSI_SR      (SSI_BASE + 0x28)
#define SSI_DR0     (SSI_BASE + 0x60)
#define SSI_SPI     (SSI_BASE + 0xF4)
#define SIZE_8      (7 << 16)
#define CTRL0_SET   (3 << 8) | (31 << 16) | (2 << 21)
#define SPI_SET1    (8 << 2) | (2 << 8) | (4 << 11) | (1 << 0)
#define SPI_SET2    (8 << 2) | (0 << 8) | (0xa0 << 24) | (4 << 11) | (2 << 0)


__attribute__((section(".boot2"), noreturn, naked, used)) void boot2() {

    // 1. Configure PADS
    clearBits(QSPI_SCLK, SCLK_MASK);
    setBits(QSPI_SCLK, FAST_8MA);

    clearBits(QSPI_SD0, SD_MASK);
    setBits(QSPI_SD0, FAST_8MA);

    clearBits(QSPI_SD1, SD_MASK);
    setBits(QSPI_SD1, FAST_8MA);

    clearBits(QSPI_SD2, SD_MASK);
    setBits(QSPI_SD2, FAST_8MA);

    clearBits(QSPI_SD3, SD_MASK);
    setBits(QSPI_SD3, FAST_8MA);

    // 2. SSI init
    
    mmio_write_32(SSI_ENR, 0x0); // Disable SSI

    mmio_write_32(SSI_BAUDR, 4); // Set divider

    mmio_write_32(SSI_CTRL0, SIZE_8); // Set 8 bit data frame

    mmio_write_32(SSI_ENR, 0x1); // Enable SSI

    mmio_write_32(SSI_DR0, 0x5);

    mmio_write_32(SSI_DR0, 0x35);

    uint32_t read_r1, read_r2;
    while(!(((read_r1 = mmio_read_32(SSI_SR)) & (1 << 2)) && !(read_r1 & (1 << 0)))); // [2] FIFO empty, [0] Busy (needs)
                                                        // Needs X1X0

    read_r1 = mmio_read_32(SSI_DR0);
    read_r2 = mmio_read_32(SSI_DR0);

    // flash -> Quad mode

    if (!(read_r2 & (1 << 1))) { // // Quad enable bit
        mmio_write_32(SSI_DR0, 0x06);
        mmio_write_32(SSI_DR0, 0x01);
        mmio_write_32(SSI_DR0, read_r1);
        mmio_write_32(SSI_DR0, read_r2 | (1 << 1));
        mmio_write_32(SSI_DR0, 0x04);
    }

    // SSI reconfigure

    mmio_write_32(SSI_ENR, 0x0);

    mmio_write_32(SSI_CTRL0, CTRL0_SET);

    mmio_write_32(SSI_SPI, SPI_SET1);

    mmio_write_32(SSI_ENR, 0x1);

    // flash teaching

    mmio_write_32(SSI_DR0, 0xEB);
    mmio_write_32(SSI_DR0, 0xA0);

    while(!(((read_r1 = mmio_read_32(SSI_SR)) & (1 << 2)) && !(read_r1 & (1 << 0))));

    // SSI recongigure again

    mmio_write_32(SSI_ENR, 0x0);

    mmio_write_32(SSI_SPI, SPI_SET2);
    
    mmio_write_32(SSI_ENR, 0x1);

    // 3. Set SP

    asm volatile("msr msp, %0" :: "r" (&_stack0_top));

    // 4. Call Reset_Handler

    Reset_Handler();

    while(1);
}