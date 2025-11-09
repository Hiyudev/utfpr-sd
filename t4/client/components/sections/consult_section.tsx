"use client";

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Leilao } from "@/lib/types";
import { calc_remaning } from "@/lib/utils";
import { useEffect, useState } from "react";
import { Button } from "../ui/button";
import { BellOffIcon, SendIcon } from "lucide-react";
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "../ui/input";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "../ui/form";

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"

const default_leiloes: Leilao[] = [
    {
        "id": "123",
        "name": "Guitarra",
        "description": "Ferramenta mágica",
        "value": 50.00,
        "start_date": new Date(),
        "end_date": new Date(new Date().getTime() + 1 * 60000)
    },
    {
        "id": "456",
        "name": "Violao",
        "description": "And his music was eletric...",
        "value": 22.00,
        "start_date": new Date(),
        "end_date": new Date(new Date().getTime() + 1 * 60000)
    }
]

const formSchema = z.object({
    lance: z.number().min(0.01, {
        error: "O valor mínimo para um leilão é R$0.01."
    })
})

export function ConsultSection() {
    const [leiloes, set_leiloes] = useState<Leilao[]>(default_leiloes);
    const [time, set_time] = useState<Date>(new Date);

    useEffect(() => {
        const interval = setInterval(() => {
            set_time(new Date());
        }, 1000);
        return () => {
            clearInterval(interval);
        };
    }, []);

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            lance: 0.01,
        },
    })

    function onLance(values: z.infer<typeof formSchema>) {
        console.log(values)
    }

    function onCancelNotification() {
        // ...
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Leilões ativos</CardTitle>
                <CardDescription>
                    Lista dos leilões que estão ativos.
                </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-6">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[100px]">Nome do produto</TableHead>
                            <TableHead>Descrição</TableHead>
                            <TableHead>Valor</TableHead>
                            <TableHead>Tempo restante</TableHead>
                            <TableHead></TableHead>
                            <TableHead></TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {leiloes.map((leilao) => (
                            <TableRow key={leilao.id}>
                                <TableCell>{leilao.name}</TableCell>
                                <TableCell>{leilao.description}</TableCell>
                                <TableCell>R${leilao.value.toFixed(2).toString()}</TableCell>
                                <TableCell>{calc_remaning(time, leilao.end_date)}</TableCell>
                                <TableCell>
                                    <Dialog>
                                        <DialogTrigger asChild>
                                            <Button variant={"outline"}>
                                                <SendIcon /> Realizar um lance
                                            </Button>
                                        </DialogTrigger>
                                        <DialogContent>
                                            <DialogHeader>
                                                <DialogTitle>Deseja realizar um lance?</DialogTitle>
                                                <DialogDescription>
                                                    Esta ação não garante que você ganhe.
                                                </DialogDescription>
                                            </DialogHeader>

                                            <Form {...form}>
                                                <form onSubmit={form.handleSubmit(onLance)} className="space-y-8">
                                                    <FormField
                                                        control={form.control}
                                                        name="lance"
                                                        render={({ field }) => (
                                                            <FormItem>
                                                                <FormLabel>Valor a ser lançado</FormLabel>
                                                                <FormControl>
                                                                    <Input type="number" step={0.01} {...field} onChange={event => field.onChange(Number(event.target.value))} />
                                                                </FormControl>
                                                                <FormDescription>
                                                                    Valor do lance.
                                                                </FormDescription>
                                                                <FormMessage />
                                                            </FormItem>
                                                        )}
                                                    />

                                                    <DialogFooter className="sm:justify-start">
                                                        <DialogClose asChild>
                                                            <Button type="submit" variant="default">
                                                                Lançar
                                                            </Button>
                                                        </DialogClose>
                                                        <DialogClose asChild>
                                                            <Button type="button" variant="secondary">
                                                                Cancelar
                                                            </Button>
                                                        </DialogClose>
                                                    </DialogFooter>
                                                </form>
                                            </Form>
                                        </DialogContent>
                                    </Dialog>
                                </TableCell>
                                <TableCell>
                                    <Button size="icon" variant={"outline"} onClick={onCancelNotification}>
                                        <BellOffIcon />
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    )
}