clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/rtl/inc -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/csr_out -incdir /home/rk6650/VeriTriples/malik2627research/rtl -incdir /home/rk6650/VeriTriples/malik2627research/rtl/inc /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/rtl/inc/dma_utils_pkg.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/rtl/inc -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/csr_out -incdir /home/rk6650/VeriTriples/malik2627research/rtl -incdir /home/rk6650/VeriTriples/malik2627research/rtl/inc /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/csr_out/csr_dma_ral_pkg.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/rtl/inc -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/csr_out -incdir /home/rk6650/VeriTriples/malik2627research/rtl -incdir /home/rk6650/VeriTriples/malik2627research/rtl/inc /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/csr_out/csr_dma.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/rtl/inc -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/csr_out -incdir /home/rk6650/VeriTriples/malik2627research/rtl -incdir /home/rk6650/VeriTriples/malik2627research/rtl/inc /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/rtl/inc/dma_pkg.svh }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/rtl/inc -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/csr_out -incdir /home/rk6650/VeriTriples/malik2627research/rtl -incdir /home/rk6650/VeriTriples/malik2627research/rtl/inc /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/rtl/dma_fifo.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/rtl/inc -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/csr_out -incdir /home/rk6650/VeriTriples/malik2627research/rtl -incdir /home/rk6650/VeriTriples/malik2627research/rtl/inc /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/csr_out/csr_dma.v }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/rtl/inc -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/csr_out -incdir /home/rk6650/VeriTriples/malik2627research/rtl -incdir /home/rk6650/VeriTriples/malik2627research/rtl/inc /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_axi_dma/rtl/dma_axi_if.sv }


            if {[catch {elaborate -top csr_dma} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/aignacio_axi_dma/misc/results.rpt
report_vacuity -out jasper_runs_6.24/aignacio_axi_dma/misc/vacuity.rpt
exit
